# Shared helpers for the san_dd_vsticam analysis (read-only; inputs under /tmp/san_dd_vsticam built by parse_dev.py and the row read)
import json, itertools
from collections import defaultdict, Counter
T = '/tmp/san_dd_vsticam'
CAM = ('camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3')
NF = 'obj_obj_relative_pos_nf'
# Name list (my guesses of the longest dimension in cm) for dev names without store-v7 size rows
NAMES = dict(alcove=150, ap=20, bananas=20, blinds=150, books=25, boots=30, bowl=15, brochures=25, bucket=35, carpet=200, chopsticks=25,
 clock=30, closet=200, column=250, couch=200, countertop=200, cupboard=150, deodorant=15, dishes=25, doorframe=210, duster=40, files=30,
 flowers=40, foosball=140, funnel=15, handle=20, hats=30, headphones=20, hearth=120, keyboard=45, knives=25, lanyard=40, laminator=45,
 lectern=120, lid=25, magazine=28, mask=20, monitor=60, mouse=11, mugs=12, notepad=25, packet=25, packets=25, painting=80, pan=40,
 papers=30, pens=15, photoframe=25, pillar=250, plant=60, powerstrip=40, razor=15, remote=18, sheet=200, shoes=30, shorts=50,
 sideboard=150, skirting=300, slippers=28, smartboard=180, stationeries=20, sticker=10, sweeper=120, tablewares=25, thermos=25,
 toilet=70, tv=110)
NAMES.update({'baby musical crib': 120, 'bath tub': 170, 'cable box': 25, 'cable concealer': 150, 'caution board': 60,
 'cleaning mop': 130, 'cleaning product': 25, 'cleaning trolley': 110, 'clothng rail': 150, 'coat hanger': 45, 'control panel': 30,
 'cooking utensils': 30, 'document holder': 30, 'dog bed': 80, 'electrical board': 50, 'face brick': 200, 'file binders': 30,
 'file folders': 30, 'fire extinquisher': 50, 'first aid kit': 30, 'flat screen display': 100, 'food supply': 40, 'game console': 30,
 'glue bottle': 15, 'hand dryer': 30, 'hand washing liquid': 20, 'hygiene products': 20, 'incense sticks packet': 25, 'instant pot': 35,
 'intercom screen': 20, 'iron board': 130, 'janitor cart': 110, 'lab fridge': 150, 'laundry detergent': 30, 'leaf fan': 50,
 'led strip': 200, 'light fixture': 60, 'light switches': 10, 'liquid soap bottle': 20, 'manual forklift': 150, 'mixer glass': 30,
 'mixer machine': 40, 'moka pot': 20, 'night lamp': 40, 'note board': 60, 'partiture stand': 120, 'phone charger': 10,
 'plastic basin': 40, 'plastic stool': 40, 'power extender': 40, 'power strip': 40, 'raised platform': 200, 'shower tub': 150,
 'skating white board': 80, 'sliding blackboards': 300, 'stove hood': 80, 'tape dispenser': 15, 'tea set': 30, 'toilet tank': 50,
 'towel rack': 60, 'trash can': 40, 'umbrella holder': 60, 'voltage stabilizer': 30, 'waffle maker': 30, 'wasching machine': 85,
 'water pot': 25, 'wet wipes': 20, 'wood stick': 100})
_M = None
def size(name, allow_list=True):
    global _M
    if _M is None: _M = json.load(open(T + '/size_medians.json'))['med']
    n = name.lower()
    if n in _M: return _M[n], 'v7'
    if allow_list and n in NAMES: return NAMES[n], 'list'
    return None, None
def dev():
    return json.load(open(T + '/dev.json'))
def rows():
    return json.load(open(T + '/rows_cam_nf.json'))
def dropped():
    s = set()
    for f in ('n.json', 'z.json'):
        for l in open('/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/' + f):
            if l.strip(): s.add(json.loads(l)['row_key'])
    return s
def argbest(cands, key, reverse=False):
    """first candidate (option order) with the min key (max if reverse); None if no key; also returns unique flag"""
    ks = [(key(c), j) for j, c in enumerate(cands) if key(c) is not None]
    if len(ks) < len(cands): return None, False
    best = max(k for k, _ in ks) if reverse else min(k for k, _ in ks)
    w = [cands[j] for k, j in ks if k == best]
    return w[0], len(w) == 1
def copeland(cands, prefs):
    """prefs: list of (nearer, farther) pairs; returns (winner or None, unique, n_pairs_used)"""
    sc = Counter(); used = 0; cs = set(cands)
    for a, b in prefs:
        if a in cs and b in cs and a != b: sc[a] += 1; sc[b] -= 1; used += 1
    if not used: return None, False, 0
    best = max(sc[c] for c in cands); w = [c for c in cands if sc[c] == best]
    return w[0], len(w) == 1, used
