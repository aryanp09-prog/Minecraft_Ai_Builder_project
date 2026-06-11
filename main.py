from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile
from panda3d.core import DirectionalLight, AmbientLight
from panda3d.core import TransparencyAttrib
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import WindowProperties
from math import pi, sin, cos
from panda3d.core import CollisionTraverser, CollisionNode, CollisionBox, CollisionRay, CollisionHandlerQueue

from ai_builder import AIBuilder
from chat_ui import ChatUI

loadPrcFile('settings.prc')

def degToRad(degrees):
    return degrees * (pi / 180.0)

# global structure ID counter
_structure_id_counter = [0]

def nextStructureId():
    _structure_id_counter[0] += 1
    return f"structure_{_structure_id_counter[0]:04d}"


class Game(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)
        self.selectedBlockType = 'grass'

        self.loadModels()
        self.setupLights()
        self.generateTerrain()
        self.setupCamera()
        self.setupSkybox()
        self.captureMouse()
        self.setupControls()

        self.playerMoveSpeed   = 10
        self.cameraSwingFactor = 10

        self.aiBuilder      = AIBuilder()
        self.buildQueue     = []
        self.buildingActive = False
        self._nextPlaceTime = 0
        self._currentBuildId = None

        # ── drag state ────────────────────────────────────────
        self.dragActive      = False    # are we dragging a structure?
        self.dragStructureId = None     # which structure are we dragging
        self.dragNodes       = []       # all NodePaths of dragged structure
        self.dragOriginalPos = []       # original positions before drag
        self.dragHoldTimer   = 0        # how long mouse1 has been held
        self.dragHoldTarget  = 0.4     # seconds to hold before drag starts
        self.mouse1Down      = False

        self.chatUI = ChatUI(self, onSubmit=self.onChatSubmit)
        taskMgr.add(self.update, 'update')

    # ----------------------------------------------------------
    # CHAT SUBMIT
    # ----------------------------------------------------------
    def onChatSubmit(self, prompt):
        for key in self.keyMap:
            self.keyMap[key] = False

        result = self.aiBuilder.process_prompt(prompt)
        if result is None:
            self.chatUI.error("Try: house, tower, pyramid, wall, castle, bridge, village or town.")
            return

        self.chatUI.companionSay(result['message'])

        originX = self.camera.getX() + (-sin(degToRad(self.camera.getH())) * 10)
        originY = self.camera.getY() + ( cos(degToRad(self.camera.getH())) * 10)
        originZ = self.camera.getZ()

        # assign one structure ID for this entire build
        self._currentBuildId = nextStructureId()

        self.buildQueue = []
        for b in result['blocks']:
            self.buildQueue.append({
                'x':    b['x'] + originX,
                'y':    b['y'] + originY,
                'z':    b['z'] + originZ,
                'type': b['type'],
                'sid':  self._currentBuildId,
            })

        if not self.buildingActive:
            self.buildingActive = True
            self._nextPlaceTime = 0
            taskMgr.add(self.liveBuildTask, 'live-build')

    # ----------------------------------------------------------
    # LIVE BUILD TASK
    # ----------------------------------------------------------
    def liveBuildTask(self, task):
        BLOCKS_PER_TICK = 2
        DELAY_SECONDS   = 0.04

        if task.time < self._nextPlaceTime:
            return task.cont

        for _ in range(BLOCKS_PER_TICK):
            if self.buildQueue:
                b = self.buildQueue.pop(0)
                self.CreateNewBlock(b['x'], b['y'], b['z'], b['type'], b.get('sid'))
            else:
                break

        if not self.buildQueue:
            self.buildingActive = False
            self.chatUI.companionSay("Done! Hold left-click on it to drag and reposition.")
            return task.done

        self._nextPlaceTime = task.time + DELAY_SECONDS
        return task.cont

    # ----------------------------------------------------------
    # UPDATE LOOP
    # ----------------------------------------------------------
    def update(self, task):
        self.cTrav.traverse(render)
        dt = globalClock.getDt()

        # ── drag hold detection ───────────────────────────────
        if self.mouse1Down and not self.dragActive:
            self.dragHoldTimer += dt
            if self.dragHoldTimer >= self.dragHoldTarget:
                self._tryStartDrag()

        # ── move dragged structure with camera ────────────────
        if self.dragActive and self.dragNodes:
            self._updateDrag()

        # ── movement ─────────────────────────────────────────
        x_movement = 0
        y_movement = 0
        z_movement = 0

        if self.keyMap["forward"]:
            x_movement -= dt * self.playerMoveSpeed * sin(degToRad(self.camera.getH()))
            y_movement += dt * self.playerMoveSpeed * cos(degToRad(self.camera.getH()))
        if self.keyMap["backward"]:
            x_movement += dt * self.playerMoveSpeed * sin(degToRad(self.camera.getH()))
            y_movement -= dt * self.playerMoveSpeed * cos(degToRad(self.camera.getH()))
        if self.keyMap["left"]:
            x_movement -= dt * self.playerMoveSpeed * cos(degToRad(self.camera.getH()))
            y_movement -= dt * self.playerMoveSpeed * sin(degToRad(self.camera.getH()))
        if self.keyMap["right"]:
            x_movement += dt * self.playerMoveSpeed * cos(degToRad(self.camera.getH()))
            y_movement += dt * self.playerMoveSpeed * sin(degToRad(self.camera.getH()))
        if self.keyMap["up"]:
            z_movement += dt * self.playerMoveSpeed
        if self.keyMap["down"]:
            z_movement -= dt * self.playerMoveSpeed

        self.camera.setPos(
            self.camera.getX() + x_movement,
            self.camera.getY() + y_movement,
            self.camera.getZ() + z_movement
        )

        if self.cameraSwingActivated:
            md           = self.win.getPointer(0)
            mouseX       = md.getX()
            mouseY       = md.getY()
            mouseChangeX = mouseX - self.lastMouseX
            mouseChangeY = mouseY - self.lastMouseY
            self.cameraSwingFactor = 10
            currentH = self.camera.getH()
            currentP = self.camera.getP()
            self.camera.setHpr(
                currentH - mouseChangeX * dt * self.cameraSwingFactor,
                min(90, max(-90, currentP - mouseChangeY * dt * self.cameraSwingFactor)),
                0
            )
            self.lastMouseX = mouseX
            self.lastMouseY = mouseY

        return task.cont

    # ----------------------------------------------------------
    # DRAG LOGIC
    # ----------------------------------------------------------
    def _tryStartDrag(self):
        """Check if crosshair is on a structure block — if so start drag."""
        if self.rayQueue.getNumEntries() == 0:
            return

        self.rayQueue.sortEntries()
        rayHit = self.rayQueue.getEntry(0)
        hitNodePath = rayHit.getIntoNodePath()
        hitObject   = hitNodePath.getPythonTag('owner')

        if hitObject is None:
            return

        sid = hitObject.getPythonTag('structure_id')
        if not sid:
            return  # terrain block — don't drag

        # collect all nodes with same structure ID
        self.dragStructureId = sid
        self.dragNodes       = []
        self.dragOriginalPos = []

        for node in render.getChildren():
            node_sid = node.getPythonTag('structure_id')
            if node_sid == sid:
                self.dragNodes.append(node)
                self.dragOriginalPos.append(node.getPos())

        if not self.dragNodes:
            return

        self.dragActive = True

        # calculate drag offset — distance in front of camera
        self.dragDistance = hitObject.getDistance(self.camera)

        # store the centre of the structure
        cx = sum(p.x for p in self.dragOriginalPos) / len(self.dragOriginalPos)
        cy = sum(p.y for p in self.dragOriginalPos) / len(self.dragOriginalPos)
        cz = sum(p.z for p in self.dragOriginalPos) / len(self.dragOriginalPos)
        self.dragCentre = (cx, cy, cz)

        self.chatUI.companionSay("Dragging structure — release click to drop!")

    def _updateDrag(self):
        """Move dragged structure to follow camera aim point."""
        # project a point 'dragDistance' units in front of camera
        h = self.camera.getH()
        p = self.camera.getP()
        fx = -sin(degToRad(h)) * cos(degToRad(p))
        fy =  cos(degToRad(h)) * cos(degToRad(p))
        fz =  sin(degToRad(p))  * -1

        dist = max(10, self.dragDistance)
        tx = self.camera.getX() + fx * dist
        ty = self.camera.getY() + fy * dist
        tz = self.dragCentre[2]   # keep original height

        # snap to grid of 2
        tx = round(tx / 2) * 2
        ty = round(ty / 2) * 2

        dx = tx - self.dragCentre[0]
        dy = ty - self.dragCentre[1]

        for i, node in enumerate(self.dragNodes):
            op = self.dragOriginalPos[i]
            node.setPos(op.x + dx, op.y + dy, op.z)

    def _dropDrag(self):
        """Drop the dragged structure at current position."""
        if not self.dragActive:
            return

        self.dragActive      = False
        self.dragStructureId = None
        self.dragNodes       = []
        self.dragOriginalPos = []
        self.chatUI.companionSay("Structure placed!")

    # ----------------------------------------------------------
    # MOUSE BUTTON HANDLERS
    # ----------------------------------------------------------
    def onMouse1Down(self):
        self.mouse1Down    = True
        self.dragHoldTimer = 0
        self.captureMouse()

    def onMouse1Up(self):
        self.mouse1Down = False
        if self.dragActive:
            self._dropDrag()
        else:
            self.removeBlock()
        self.dragHoldTimer = 0

    # ----------------------------------------------------------
    # CONTROLS
    # ----------------------------------------------------------
    def setupControls(self):
        self.keyMap = {
            "forward": False, "backward": False,
            "left": False,    "right": False,
            "up": False,      "down": False,
        }
        self.accept('escape',      self.releaseMouse)
        self.accept('mouse1',      self.onMouse1Down)
        self.accept('mouse1-up',   self.onMouse1Up)
        self.accept('mouse3',      self.PlaceBlock)
        self.accept('w',           self.updateKeyMap, ['forward',  True])
        self.accept('w-up',        self.updateKeyMap, ['forward',  False])
        self.accept('a',           self.updateKeyMap, ['left',     True])
        self.accept('a-up',        self.updateKeyMap, ['left',     False])
        self.accept('s',           self.updateKeyMap, ['backward', True])
        self.accept('s-up',        self.updateKeyMap, ['backward', False])
        self.accept('d',           self.updateKeyMap, ['right',    True])
        self.accept('d-up',        self.updateKeyMap, ['right',    False])
        self.accept('space',       self.updateKeyMap, ['up',       True])
        self.accept('space-up',    self.updateKeyMap, ['up',       False])
        self.accept('lshift',      self.updateKeyMap, ['down',     True])
        self.accept('lshift-up',   self.updateKeyMap, ['down',     False])
        self.accept('1', self.setSelectedBlockType, ['grass'])
        self.accept('2', self.setSelectedBlockType, ['dirt'])
        self.accept('3', self.setSelectedBlockType, ['sand'])
        self.accept('4', self.setSelectedBlockType, ['stone'])
        self.accept('5', self.setSelectedBlockType, ['wood'])
        self.accept('6', self.setSelectedBlockType, ['brick'])

    def setSelectedBlockType(self, type):
        self.selectedBlockType = type
        print("Selected block:", type)

    def updateKeyMap(self, key, value):
        self.keyMap[key] = value

    # ----------------------------------------------------------
    # BLOCK REMOVE / PLACE
    # ----------------------------------------------------------
    def removeBlock(self):
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit      = self.rayQueue.getEntry(0)
            hitNodePath = rayHit.getIntoNodePath()
            hitObject   = hitNodePath.getPythonTag('owner')
            if hitObject and hitObject.getDistance(self.camera) < 12:
                hitNodePath.clearPythonTag('owner')
                hitObject.removeNode()

    def PlaceBlock(self):
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit      = self.rayQueue.getEntry(0)
            hitNodePath = rayHit.getIntoNodePath()
            normal      = rayHit.getSurfaceNormal(hitNodePath)
            hitObject   = hitNodePath.getPythonTag('owner')
            if hitObject and hitObject.getDistance(self.camera) < 12:
                newBlockPos = hitObject.getPos() + normal * 2
                self.CreateNewBlock(newBlockPos.x, newBlockPos.y, newBlockPos.z, self.selectedBlockType)

    # ----------------------------------------------------------
    # MOUSE
    # ----------------------------------------------------------
    def captureMouse(self):
        self.cameraSwingActivated = True
        md = self.win.getPointer(0)
        self.lastMouseX = md.getX()
        self.lastMouseY = md.getY()
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(props)

    def releaseMouse(self):
        self.cameraSwingActivated = False
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(props)

    # ----------------------------------------------------------
    # CAMERA
    # ----------------------------------------------------------
    def setupCamera(self):
        self.disableMouse()
        self.camera.setPos(0, -10, 2)
        self.camLens.setFov(80)
        crosshairs = OnscreenImage(
            image='crosshairs.png', pos=(0, 0, 0), scale=0.05,
        )
        crosshairs.setTransparency(TransparencyAttrib.MAlpha)
        self.cTrav    = CollisionTraverser()
        ray           = CollisionRay()
        ray.setFromLens(self.camNode, (0, 0))
        rayNode       = CollisionNode('line-of-sight')
        rayNode.addSolid(ray)
        rayNodePath   = self.camera.attachNewNode(rayNode)
        self.rayQueue = CollisionHandlerQueue()
        self.cTrav.addCollider(rayNodePath, self.rayQueue)

    def setupSkybox(self):
        skybox = loader.loadModel('skybox/skybox.egg')
        skybox.setScale(500)
        skybox.setBin('background', 1)
        skybox.setDepthWrite(0)
        skybox.setLightOff()
        skybox.reparentTo(render)

    def generateTerrain(self):
        for z in range(2):
            for y in range(40):
                for x in range(40):
                    self.CreateNewBlock(
                        x * 2 - 40, y * 2 - 40, -z * 2,
                        'grass' if z == 0 else 'dirt',
                        sid=None   # terrain has no structure ID
                    )

    # ----------------------------------------------------------
    # CREATE BLOCK  — now accepts structure ID
    # ----------------------------------------------------------
    def CreateNewBlock(self, x, y, z, type, sid=None):
        newBlockNode = render.attachNewNode('new-block-placeholder')
        newBlockNode.setPos(x, y, z)

        if type == 'grass':   self.grassBlock.instanceTo(newBlockNode)
        elif type == 'dirt':  self.dirtBlock.instanceTo(newBlockNode)
        elif type == 'sand':  self.sandBlock.instanceTo(newBlockNode)
        elif type == 'stone': self.stoneBlock.instanceTo(newBlockNode)
        elif type == 'wood':  self.woodBlock.instanceTo(newBlockNode)
        elif type == 'brick': self.brickBlock.instanceTo(newBlockNode)
        else:                 self.stoneBlock.instanceTo(newBlockNode)

        # tag with structure ID for drag selection
        if sid:
            newBlockNode.setPythonTag('structure_id', sid)

        blockSolid = CollisionBox((-1, -1, -1), (1, 1, 1))
        blockNode  = CollisionNode('block-collison-node')
        blockNode.addSolid(blockSolid)
        collider   = newBlockNode.attachNewNode(blockNode)
        collider.setPythonTag('owner',        newBlockNode)
        collider.setPythonTag('structure_id', sid)

        return newBlockNode

    # ----------------------------------------------------------
    # MODELS
    # ----------------------------------------------------------
    def _loadNormalized(self, path, scale_mult=1.0):
        model = loader.loadModel(path)
        bounds = model.getTightBounds()
        if bounds:
            mn, mx = bounds
            size = max(mx - mn)
            if size > 0:
                model.setScale((2.0 / size) * scale_mult)
        model.setP(90)
        return model

    def loadModels(self):
        self.grassBlock = self._loadNormalized('grass-block.glb')
        self.dirtBlock  = self._loadNormalized('dirt-block.glb')
        self.stoneBlock = self._loadNormalized('stone-block.glb')
        self.sandBlock  = self._loadNormalized('sand-block.glb')
        self.woodBlock  = self._loadNormalized('wood-block.glb')
        self.brickBlock = self._loadNormalized('brick-block.glb')

    # ----------------------------------------------------------
    # LIGHTS
    # ----------------------------------------------------------
    def setupLights(self):
        mainLight            = DirectionalLight('main light')
        mainLightNodePath    = render.attachNewNode(mainLight)
        mainLightNodePath.setHpr(30, -60, 0)
        render.setLight(mainLightNodePath)
        ambientLight         = AmbientLight('ambient light')
        ambientLight.setColor((0.3, 0.3, 0.3, 1))
        ambientLightNodePath = render.attachNewNode(ambientLight)
        render.setLight(ambientLightNodePath)


game = Game()
game.run()
