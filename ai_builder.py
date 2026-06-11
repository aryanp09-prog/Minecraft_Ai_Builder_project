# =============================================================
#  ai_builder.py  —  AI Builder with compound prompt support
#  Handles prompts like:
#    "build a bridge and a house next to it"
#    "make a castle with a tower beside it"
#    "create a village and a pyramid"
# =============================================================

import os
import pickle
import re

SIZE_MAP = {
    'tiny':   0.5,
    'small':  0.75,
    'normal': 1.0,
    'big':    1.5,
    'huge':   2.0,
}

STYLE_DEFAULTS = {
    'modern':   'stone',
    'medieval': 'stone',
    'wooden':   'wood',
    'classic':  'stone',
    'simple':   'stone',
    'fancy':    'stone',
    'natural':  'wood',
    'forest':   'wood',
    'desert':   'sand',
    'jungle':   'wood',
}

# Keywords that signal a second structure in compound prompts
COMPOUND_SPLITTERS = [
    ' and a ', ' and an ', ' and the ',
    ' and ', ' with a ', ' with an ',
    ' next to a ', ' beside a ', ' near a ',
    ' also a ', ' plus a ', ' along with a ',
]


# ── Trained ML Parser ─────────────────────────────────────────

class TrainedParser:
    def __init__(self):
        with open('model.pkl', 'rb') as f:
            bundle = pickle.load(f)
        self.intent_model   = bundle['intent']
        self.size_model     = bundle['size']
        self.material_model = bundle['material']
        print("Trained AI model loaded successfully.")

    def parse(self, prompt):
        p = prompt.lower()

        if any(w in p for w in ['village', 'hamlet', 'settlement']):
            intent = 'village'
        elif any(w in p for w in ['town', 'city', 'township']):
            intent = 'town'
        elif any(w in p for w in ['castle', 'fortress', 'fort', 'stronghold']):
            intent = 'castle'
        elif any(w in p for w in ['bridge', 'overpass', 'span', 'crossing']):
            intent = 'bridge'
        else:
            intent = self.intent_model.predict([p])[0]

        size_lbl = self.size_model.predict([p])[0]
        material = self.material_model.predict([p])[0]

        for keyword, default_mat in STYLE_DEFAULTS.items():
            if keyword in p and material == 'stone':
                material = default_mat
                break

        return {
            'intent':   intent,
            'size':     SIZE_MAP.get(size_lbl, 1.0),
            'material': material,
        }


# ── Rule-based Fallback Parser ─────────────────────────────────

class RuleParser:
    SIZE_KEYWORDS = {
        'tiny': 0.5, 'small': 0.75, 'big': 1.5,
        'large': 1.5, 'huge': 2.0, 'giant': 2.5,
    }
    MATERIAL_KEYWORDS = {
        'grass': 'grass', 'dirt': 'dirt', 'sand': 'sand',
        'stone': 'stone', 'rock': 'stone',
        'wood': 'wood', 'wooden': 'wood', 'plank': 'wood',
        'brick': 'brick', 'bricks': 'brick',
    }
    STRUCTURE_KEYWORDS = {
        'house': 'house', 'home': 'house', 'cabin': 'house', 'hut': 'house',
        'tower': 'tower', 'pillar': 'tower',
        'pyramid': 'pyramid',
        'wall': 'wall', 'fence': 'wall', 'barrier': 'wall',
        'castle': 'castle', 'fortress': 'castle', 'fort': 'castle',
        'bridge': 'bridge', 'overpass': 'bridge', 'crossing': 'bridge',
        'village': 'village', 'hamlet': 'village', 'settlement': 'village',
        'town': 'town', 'city': 'town', 'township': 'town',
    }

    def parse(self, prompt):
        words    = prompt.lower().split()
        intent   = None
        size     = 1.0
        material = 'stone'
        for word in words:
            if word in self.STRUCTURE_KEYWORDS: intent   = self.STRUCTURE_KEYWORDS[word]
            if word in self.SIZE_KEYWORDS:      size     = self.SIZE_KEYWORDS[word]
            if word in self.MATERIAL_KEYWORDS:  material = self.MATERIAL_KEYWORDS[word]
        for keyword, default_mat in STYLE_DEFAULTS.items():
            if keyword in prompt.lower() and material == 'stone':
                material = default_mat
                break
        return {'intent': intent, 'size': size, 'material': material}


# ── Compound Prompt Splitter ───────────────────────────────────

class CompoundSplitter:
    """
    Detects compound prompts and splits them into sub-prompts.
    e.g. "build a bridge and a house next to it"
      → ["build a bridge", "build a house next to it"]
    """

    def split(self, prompt):
        p = prompt.lower().strip()

        # try each splitter keyword
        for splitter in COMPOUND_SPLITTERS:
            if splitter in p:
                parts = p.split(splitter, 1)
                part1 = parts[0].strip()
                part2 = parts[1].strip()

                # clean up "next to it", "beside it" etc from part2
                part2 = re.sub(r'\b(next to it|beside it|near it|next to|'
                               r'beside|nearby|close by)\b', '', part2).strip()

                # make sure part2 has a build verb
                if not any(part2.startswith(v) for v in
                           ['build', 'make', 'create', 'construct']):
                    part2 = 'build a ' + part2

                return [part1, part2]

        # no compound found — return single prompt
        return [prompt]


# ── Shape Generator ────────────────────────────────────────────

class ShapeGenerator:

    def generate(self, intent, size, material):
        if intent == 'house':   return self._house(size, material)
        if intent == 'tower':   return self._tower(size, material)
        if intent == 'pyramid': return self._pyramid(size, material)
        if intent == 'wall':    return self._wall(size, material)
        if intent == 'castle':  return self._castle(size, material)
        if intent == 'bridge':  return self._bridge(size, material)
        if intent == 'village': return self._village(size, material)
        if intent == 'town':    return self._town(size, material)
        return []

    def _offset_blocks(self, blocks, ox, oy):
        return [
            {'x': b['x'] + ox*2, 'y': b['y'] + oy*2, 'z': b['z'], 'type': b['type']}
            for b in blocks
        ]

    def _get_footprint(self, blocks):
        """Returns max x and y extent of a block list in grid units."""
        if not blocks:
            return 0, 0
        max_x = max(b['x'] for b in blocks) // 2 + 1
        max_y = max(b['y'] for b in blocks) // 2 + 1
        return max_x, max_y

    # ----------------------------------------------------------
    def _house(self, size, material):
        blocks = []
        width  = max(5, int(7 * size))
        depth  = max(5, int(7 * size))
        height = max(4, int(5 * size))
        if width  % 2 == 0: width  += 1
        if depth  % 2 == 0: depth  += 1
        mid_z = height // 2

        for z in range(height):
            for x in range(width):
                for y in range(depth):
                    is_edge   = (x==0 or x==width-1 or y==0 or y==depth-1)
                    is_roof   = (z == height-1)
                    is_floor  = (z == 0)
                    is_corner = ((x==0 or x==width-1) and (y==0 or y==depth-1))
                    is_door   = (y==0 and x==width//2 and z < 2)
                    is_window = (
                        z == mid_z and not is_corner and
                        (
                            (x==0 and y in range(1, depth-1)) or
                            (x==width-1 and y in range(1, depth-1)) or
                            (y==depth-1 and x in range(1, width-1))
                        )
                    )
                    if not (is_floor or is_roof or is_edge): continue
                    if is_door or is_window: continue
                    if is_floor:        block_type = 'stone'
                    elif is_roof:       block_type = 'wood'
                    elif is_corner:     block_type = 'stone'
                    else:               block_type = material
                    blocks.append({'x': x*2, 'y': y*2, 'z': z*2, 'type': block_type})
        return blocks

    def _tower(self, size, material):
        blocks = []
        width  = max(3, int(5  * size))
        height = max(5, int(12 * size))
        if width % 2 == 0: width += 1
        for z in range(height):
            for x in range(width):
                for y in range(width):
                    is_edge  = (x==0 or x==width-1 or y==0 or y==width-1)
                    is_roof  = (z == height-1)
                    is_floor = (z == 0)
                    is_door  = (y==0 and x==width//2 and z < 2)
                    is_window = (z % 3 == 2 and is_edge and
                                 not (x==0 and y==0) and not (x==0 and y==width-1) and
                                 not (x==width-1 and y==0) and not (x==width-1 and y==width-1))
                    if not (is_edge or is_roof or is_floor): continue
                    if is_door or is_window: continue
                    if is_floor or is_roof: block_type = 'stone'
                    elif z % 4 == 0:        block_type = 'stone'
                    else:                   block_type = material
                    blocks.append({'x': x*2, 'y': y*2, 'z': z*2, 'type': block_type})
        return blocks

    def _pyramid(self, size, material):
        blocks = []
        base   = max(3, int(9 * size))
        if base % 2 == 0: base += 1
        layers = (base + 1) // 2
        for z in range(layers):
            layer_size = base - z * 2
            offset     = z
            block_type = material if z % 2 == 0 else 'stone'
            for x in range(layer_size):
                for y in range(layer_size):
                    blocks.append({'x': (x+offset)*2, 'y': (y+offset)*2, 'z': z*2, 'type': block_type})
        return blocks

    def _wall(self, size, material):
        blocks = []
        length = max(5, int(15 * size))
        height = max(3, int(5  * size))
        for x in range(length):
            for z in range(height):
                block_type = 'stone' if z == 0 else material
                blocks.append({'x': x*2, 'y': 0, 'z': z*2, 'type': block_type})
        return blocks

    def _castle(self, size, material):
        blocks  = []
        base    = max(12, int(18 * size))
        if base % 2 == 0: base += 1
        wall_h  = max(5, int(7  * size))
        tower_h = wall_h + max(3, int(4 * size))
        tower_w = max(3, int(4  * size))
        if tower_w % 2 == 0: tower_w += 1
        for x in range(base):
            for z in range(wall_h):
                for y in [0, base-1]:
                    is_gate = (y==0 and abs(x-base//2)<=1 and z < wall_h-2)
                    if not is_gate:
                        blocks.append({'x': x*2, 'y': y*2, 'z': z*2, 'type': material})
        for y in range(1, base-1):
            for z in range(wall_h):
                for x in [0, base-1]:
                    blocks.append({'x': x*2, 'y': y*2, 'z': z*2, 'type': material})
        for x in range(base):
            if x % 2 == 0:
                for y in [0, base-1]:
                    blocks.append({'x': x*2, 'y': y*2, 'z': wall_h*2, 'type': material})
        for y in range(base):
            if y % 2 == 0:
                for x in [0, base-1]:
                    blocks.append({'x': x*2, 'y': y*2, 'z': wall_h*2, 'type': material})
        corners = [(0,0),(0,base-tower_w),(base-tower_w,0),(base-tower_w,base-tower_w)]
        for (cx, cy) in corners:
            for z in range(tower_h):
                for tx in range(tower_w):
                    for ty in range(tower_w):
                        is_edge  = (tx==0 or tx==tower_w-1 or ty==0 or ty==tower_w-1)
                        is_floor = (z == 0)
                        is_roof  = (z == tower_h-1)
                        if not (is_edge or is_floor or is_roof): continue
                        blocks.append({'x': (cx+tx)*2, 'y': (cy+ty)*2, 'z': z*2, 'type': material})
            for tx in range(tower_w):
                if tx % 2 == 0:
                    for ty in [0, tower_w-1]:
                        blocks.append({'x': (cx+tx)*2, 'y': (cy+ty)*2, 'z': tower_h*2, 'type': material})
            for ty in range(tower_w):
                if ty % 2 == 0:
                    for tx in [0, tower_w-1]:
                        blocks.append({'x': (cx+tx)*2, 'y': (cy+ty)*2, 'z': tower_h*2, 'type': material})
        for x in range(1, base-1):
            for y in range(1, base-1):
                blocks.append({'x': x*2, 'y': y*2, 'z': 0, 'type': 'stone'})
        return blocks

    def _bridge(self, size, material):
        blocks = []
        length = max(10, int(20 * size))
        width  = max(3,  int(5  * size))
        height = max(4,  int(6  * size))
        if width % 2 == 0: width += 1
        for x in range(length):
            for y in range(width):
                blocks.append({'x': x*2, 'y': y*2, 'z': height*2, 'type': material})
        for x in range(length):
            for z in [height+1, height+2]:
                blocks.append({'x': x*2, 'y': 0,           'z': z*2, 'type': material})
                blocks.append({'x': x*2, 'y': (width-1)*2, 'z': z*2, 'type': material})
        for x in range(0, length, 4):
            for z in range(0, height):
                for y in range(width):
                    if y == 0 or y == width-1:
                        blocks.append({'x': x*2, 'y': y*2, 'z': z*2, 'type': 'stone'})
        for px in range(0, length-4, 4):
            mid_x  = px + 2
            arch_z = height - 1
            for y in [0, width-1]:
                blocks.append({'x': mid_x*2, 'y': y*2, 'z': arch_z*2, 'type': 'stone'})
        return blocks

    def _village(self, size, material):
        blocks = []
        gap    = 6
        house_w = max(5, int(7 * size))
        if house_w % 2 == 0: house_w += 1

        centre_house = self._house(size, material)
        blocks += centre_house

        left_house = self._house(size * 0.75, 'wood')
        left_house = self._offset_blocks(left_house, -(house_w + gap), 0)
        blocks += left_house

        right_house = self._house(size * 0.75, 'wood')
        right_house = self._offset_blocks(right_house, house_w + gap, 0)
        blocks += right_house

        tower = self._tower(size * 0.8, 'stone')
        tower = self._offset_blocks(tower, house_w + gap, house_w + gap)
        blocks += tower

        wall_length = (house_w + gap) * 2 + house_w
        wall_h = max(3, int(4 * size))
        back_wall = []
        for x in range(wall_length):
            for z in range(wall_h):
                block_type = 'stone' if z == 0 else material
                back_wall.append({'x': x*2, 'y': 0, 'z': z*2, 'type': block_type})
        back_wall = self._offset_blocks(back_wall, -(house_w + gap), house_w + gap)
        blocks += back_wall

        return blocks

    def _town(self, size, material):
        blocks  = []
        gap     = 8
        house_w = max(5, int(7 * size))
        if house_w % 2 == 0: house_w += 1
        spacing = house_w + gap

        house_materials = ['wood', material, material, 'wood']
        positions = [(0,0),(spacing,0),(0,spacing),(spacing,spacing)]
        for i, (ox, oy) in enumerate(positions):
            h = self._house(size * 0.9, house_materials[i])
            h = self._offset_blocks(h, ox, oy)
            blocks += h

        tower1 = self._tower(size * 0.7, 'stone')
        tower1 = self._offset_blocks(tower1, -gap, -gap)
        blocks += tower1

        tower2 = self._tower(size * 0.7, 'stone')
        tower2 = self._offset_blocks(tower2, spacing*2, spacing*2)
        blocks += tower2

        path_len = spacing
        for x in range(path_len):
            blocks.append({'x': (x + house_w)*2, 'y': (house_w//2)*2, 'z': 0, 'type': 'stone'})
        for y in range(path_len):
            blocks.append({'x': (house_w//2)*2, 'y': (y + house_w)*2, 'z': 0, 'type': 'stone'})

        total  = spacing * 2 + house_w
        wall_h = max(3, int(4 * size))
        offset = gap // 2
        for x in range(total + gap):
            for z in range(wall_h):
                t = 'stone' if z == 0 else material
                if not (abs(x - (total+gap)//2) <= 1 and z < 2):
                    blocks.append({'x': (x-offset)*2, 'y': (-offset)*2,      'z': z*2, 'type': t})
                blocks.append({'x': (x-offset)*2, 'y': (total+offset)*2, 'z': z*2, 'type': t})
        for y in range(total + gap):
            for z in range(wall_h):
                t = 'stone' if z == 0 else material
                blocks.append({'x': (-offset)*2,      'y': (y-offset)*2, 'z': z*2, 'type': t})
                blocks.append({'x': (total+offset)*2, 'y': (y-offset)*2, 'z': z*2, 'type': t})
        return blocks


# ── Main AIBuilder ─────────────────────────────────────────────

class AIBuilder:

    # gap between compound structures in grid units
    COMPOUND_GAP = 20

    def __init__(self):
        self.generator = ShapeGenerator()
        self.splitter  = CompoundSplitter()
        if os.path.exists('model.pkl'):
            self.parser = TrainedParser()
        else:
            print("model.pkl not found — using rule-based parser.")
            self.parser = RuleParser()

    def process_prompt(self, prompt):
        # ── detect compound prompt ────────────────────────────
        parts = self.splitter.split(prompt)

        if len(parts) == 1:
            # single structure — normal flow
            return self._build_single(prompt, offset_x=0, offset_y=0)

        # ── compound: build each part with spacing ────────────
        all_blocks = []
        messages   = []
        current_x  = 0

        for part in parts:
            result = self._build_single(part, offset_x=current_x, offset_y=0)
            if result:
                all_blocks += result['blocks']
                messages.append(result['message'])
                # advance x offset so next structure doesn't overlap
                if result['blocks']:
                    max_x = max(b['x'] for b in result['blocks']) // 2 + 1
                    current_x += max_x + self.COMPOUND_GAP

        if not all_blocks:
            return None

        combined_message = ' + '.join(messages)
        return {
            'blocks':  all_blocks,
            'message': combined_message,
        }

    def _build_single(self, prompt, offset_x, offset_y):
        parsed = self.parser.parse(prompt)
        if parsed['intent'] is None:
            return None

        blocks = self.generator.generate(
            parsed['intent'], parsed['size'], parsed['material']
        )

        # apply offset
        blocks = [
            {
                'x':    b['x'] + offset_x * 2,
                'y':    b['y'] + offset_y * 2,
                'z':    b['z'],
                'type': b['type']
            }
            for b in blocks
        ]

        message = (
            f"{self._size_label(parsed['size'])}"
            f"{parsed['material']} {parsed['intent']} "
            f"({len(blocks)} blocks)"
        )
        return {'blocks': blocks, 'message': message}

    def _size_label(self, size):
        if size <= 0.5:  return 'tiny '
        if size <= 0.75: return 'small '
        if size <= 1.0:  return ''
        if size <= 1.5:  return 'large '
        return 'huge '
