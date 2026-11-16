"""Names the teacher prompts per capture: GT names, listed confusers and absent names (design 3.1 step 1).

GT names: normalized labels of instances visible (>= MIN_PX pixels on the 240x320 raster) in at least one anchor
frame; structural and generic labels are dropped; at most MAX_GT names, by visible pixel total, operands first.
Confusers: names from the confusion groups of present names that GT does not hold, up to N_CONF (then frequent
vocabulary names of the same dataset absent from GT). Absent: N_ABSENT names of the dataset's annotated vocabulary
absent from GT, drawn with a per-capture seed. ARKitScenes annotates 17 classes only, so its confusers and absent
names come from that list (a name outside it can be present but unannotated).
"""
from __future__ import annotations

import hashlib
import random

import numpy as np

from .common import normalize_name

MIN_PX = 20
MAX_GT = 16
N_CONF = 4
N_ABSENT = 2
STRUCTURAL = {'wall', 'floor', 'ceiling', 'object', 'otherfurniture', 'otherstructure', 'otherprop', 'remove',
              'split', 'unknown', 'objects', 'stuff', 'structure', 'clutter', 'wall hanging'}
LABEL_FIX = {'tv monitor': 'tv'}
ARKIT17 = ['cabinet', 'refrigerator', 'shelf', 'stove', 'bed', 'sink', 'washer', 'toilet', 'bathtub', 'oven',
           'dishwasher', 'fireplace', 'stool', 'chair', 'table', 'tv', 'sofa']
# Groups of names the benchmark's operands confuse (cabinet and nightstand is the design's example).
CONFUSER_GROUPS = [
    ['cabinet', 'nightstand', 'dresser', 'kitchen cabinet', 'drawer', 'wardrobe', 'shelf', 'bookshelf'],
    ['table', 'desk', 'coffee table', 'nightstand', 'counter', 'kitchen counter', 'side table'],
    ['chair', 'stool', 'armchair', 'office chair', 'sofa chair', 'bench'],
    ['sofa', 'couch', 'bed', 'armchair', 'ottoman'],
    ['tv', 'monitor', 'computer', 'laptop', 'picture', 'whiteboard'],
    ['door', 'window', 'closet door', 'cabinet door', 'doorframe', 'mirror'],
    ['trash can', 'trash bin', 'bucket', 'box', 'basket', 'laundry basket'],
    ['lamp', 'light', 'ceiling light', 'table lamp', 'ceiling lamp'],
    ['pillow', 'cushion', 'towel', 'blanket', 'clothing', 'bag'],
    ['curtain', 'window blind', 'blinds', 'shower curtain'],
    ['sink', 'bathtub', 'toilet', 'shower', 'washer', 'dishwasher'],
    ['refrigerator', 'oven', 'stove', 'microwave', 'dishwasher', 'washer', 'cabinet'],
    ['plant', 'vase', 'potted plant', 'flower pot'],
    ['bottle', 'cup', 'mug', 'vase', 'jar'],
    ['radiator', 'heater', 'fireplace', 'air conditioner'],
]


def prompt_name(label: str) -> str:
    n = normalize_name(label)
    return LABEL_FIX.get(n, n)


def confusers_of(name):
    out = []
    for g in CONFUSER_GROUPS:
        if name in g:
            out += [x for x in g if x != name]
    return list(dict.fromkeys(out))


def gt_visible_names(npz, min_px=MIN_PX):
    """{name: visible pixel total over frames}, {name: [instance ids]} from a GT raster npz."""
    inst = npz['inst']
    lab = {int(i): prompt_name(str(l)) for i, l in zip(npz['ids'], npz['labels'])}
    ids, counts = np.unique(inst[inst >= 0], return_counts=True)
    px, members = {}, {}
    for i, c in zip(ids.tolist(), counts.tolist()):
        n = lab.get(i)
        if n is None or n in STRUCTURAL or c < min_px:
            continue
        px[n] = px.get(n, 0) + c
        members.setdefault(n, []).append(i)
    return px, members, set(lab.values())


def capture_names(canonical, npz, operands=(), vocab_by_ds=None):
    ds = canonical.split('/')[0]
    px, members, annotated = gt_visible_names(npz)
    ops = [prompt_name(o) for o in operands]
    order = [o for o in ops if o in px] + sorted((n for n in px if n not in ops), key=lambda n: (-px[n], n))
    gt = list(dict.fromkeys(order))[:MAX_GT]
    rng = random.Random(int(hashlib.sha256(f'owngrd names v1 {canonical}'.encode()).hexdigest()[:12], 16))
    universe = ARKIT17 if ds == 'arkitscenes' else list((vocab_by_ds or {}).get(ds, []))
    conf = []
    for n in gt:
        for c in confusers_of(n):
            if c not in annotated and c not in conf and (ds != 'arkitscenes' or c in ARKIT17):
                conf.append(c)
    rng.shuffle(conf)
    conf = conf[:N_CONF]
    pool = [n for n in universe if n not in annotated and n not in conf and n not in STRUCTURAL]
    if len(conf) < N_CONF:
        extra = pool[:]
        rng.shuffle(extra)
        conf += extra[:N_CONF - len(conf)]
    pool = [n for n in pool if n not in conf]
    rng.shuffle(pool)
    absent = pool[:N_ABSENT]
    names = [{'name': n, 'role': 'gt', 'instances': sorted(members[n])} for n in gt]
    names += [{'name': n, 'role': 'confuser', 'instances': []} for n in conf]
    names += [{'name': n, 'role': 'absent', 'instances': []} for n in absent]
    return names
