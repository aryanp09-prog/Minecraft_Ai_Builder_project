# =============================================================
#  generate_data.py  —  Training data including village + town
# =============================================================

import csv
import random

INTENTS = ['house', 'tower', 'pyramid', 'wall', 'castle', 'bridge', 'village', 'town']

SIZE_WORDS = {
    'tiny': 'tiny', 'small': 'small', 'big': 'big',
    'large': 'big', 'huge': 'huge', 'giant': 'huge', '': 'normal',
}

MATERIAL_WORDS = {
    'grass': 'grass', 'dirt': 'dirt', 'sand': 'sand',
    'stone': 'stone', 'rock': 'stone',
    'wood': 'wood', 'wooden': 'wood', 'plank': 'wood',
    'brick': 'brick', '': 'stone',
}

INTENT_SYNONYMS = {
    'house':   ['house', 'home', 'cabin', 'hut', 'cottage', 'building'],
    'tower':   ['tower', 'pillar', 'spire', 'column', 'obelisk'],
    'pyramid': ['pyramid', 'triangle'],
    'wall':    ['wall', 'fence', 'barrier', 'partition'],
    'castle':  ['castle', 'fortress', 'fort', 'stronghold', 'citadel'],
    'bridge':  ['bridge', 'overpass', 'crossing', 'span', 'walkway'],
    'village': ['village', 'hamlet', 'settlement', 'camp', 'outpost'],
    'town':    ['town', 'city', 'township', 'district', 'borough'],
}

ACTION_WORDS = [
    'build', 'make', 'create', 'construct',
    'build me', 'make me', 'i want a',
    'can you build', 'please build', 'generate',
]

FILLER = ['', 'please', 'now', 'here', 'for me', 'quickly']


def make_prompt(action, size, material, synonym, filler):
    parts = [action]
    if size:     parts.append(size)
    if material: parts.append(material)
    parts.append(synonym)
    if filler:   parts.append(filler)
    return ' '.join(parts).strip().lower()


rows = []

for intent in INTENTS:
    for action in ACTION_WORDS:
        for size_word, size_label in SIZE_WORDS.items():
            for mat_word, mat_label in MATERIAL_WORDS.items():
                for synonym in INTENT_SYNONYMS[intent]:
                    for filler in FILLER:
                        prompt = make_prompt(action, size_word, mat_word, synonym, filler)
                        rows.append({
                            'prompt':   prompt,
                            'intent':   intent,
                            'size':     size_label,
                            'material': mat_label,
                        })

random.shuffle(rows)

with open('training_data.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['prompt', 'intent', 'size', 'material'])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} training examples → training_data.csv")
