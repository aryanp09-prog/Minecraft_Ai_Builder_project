# =============================================================
#  companion.py  —  Lightweight companion
#  Uses the existing stone block model as a placeholder body.
#  Zero custom geometry, minimal CPU usage.
# =============================================================

from math import sin, cos, pi


def _deg2rad(d):
    return d * (pi / 180.0)


class Companion:

    def __init__(self, game):
        self.game       = game
        self.isBuilding = False
        self._bobTime   = 0
        self._buildModel()
        taskMgr.add(self._update, 'companion-update')

    def _buildModel(self):
        # root node
        self.model = render.attachNewNode('companion-root')

        # reuse the already-loaded stone block as the body
        body = render.attachNewNode('companion-body')
        game = self.game
        game.stoneBlock.instanceTo(body)
        body.setScale(0.6, 0.6, 1.0)
        body.reparentTo(self.model)
        body.setZ(0.5)

        # head — reuse grass block
        head = render.attachNewNode('companion-head')
        game.grassBlock.instanceTo(head)
        head.setScale(0.55)
        head.reparentTo(self.model)
        head.setZ(1.6)

        print("Companion ready.")

    def _update(self, task):
        dt             = globalClock.getDt()
        self._bobTime += dt

        cam = self.game.camera
        h   = cam.getH()
        fx  = -sin(_deg2rad(h))
        fy  =  cos(_deg2rad(h))
        rx  =  cos(_deg2rad(h))
        ry  =  sin(_deg2rad(h))

        cx = cam.getX() + fx * 3 + rx * 4
        cy = cam.getY() + fy * 3 + ry * 4
        cz = cam.getZ() - 1.5

        bob = sin(self._bobTime * (4 if self.isBuilding else 1.5)) * 0.1

        self.model.setPos(cx, cy, cz + bob)

        if self.isBuilding:
            self.model.setH(self.model.getH() + dt * 90)
        else:
            self.model.setH(h + 180)

        return task.cont

    def startBuilding(self):
        self.isBuilding = True

    def stopBuilding(self):
        self.isBuilding = False
