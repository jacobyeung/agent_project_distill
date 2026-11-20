"""toolprog: question parsing, geometry primitives and VSI-Bench / VSTI scoring shared by every condition.

World/meta geometry is z-up metres. Floor-plane rule: u = F - S, v = Q - S on the floor; cross = u_x v_y - u_y v_x in a
right-handed z-up frame (cross > 0: left), dot > 0: front; theta = atan2(cross, dot) in degrees.
"""
import math
import re

import numpy as np

MRA_THRESHOLDS = np.arange(0.5, 0.951, 0.05)


def mra(pred, gt):
    if pred is None or gt is None or not np.isfinite(pred):
        return 0.0
    gt = float(gt)
    rel = abs(float(pred) - gt) / abs(gt) if gt else (0.0 if pred == 0 else 1.0)
    return float(np.mean([rel < 1.0 - t for t in MRA_THRESHOLDS]))


def score(qtype, pred, gt):
    if qtype in NUMERIC:
        return mra(pred, float(gt))
    return float(pred is not None and str(pred).strip().upper() == str(gt).strip().upper())


NUMERIC = {'object_abs_distance', 'object_counting', 'object_size_estimation', 'room_size_estimation',
           'camera_displacement', 'camera_obj_abs_dist'}


def letter_of(options, text):
    """Option letter whose text equals `text` (case/space-insensitive)."""
    norm = lambda s: re.sub(r'\s+', ' ', s.strip().lower().rstrip('.'))
    for o in options:
        m = re.match(r'^([A-Z])\.\s*(.*)$', o.strip())
        if m and norm(m.group(2)) == norm(text):
            return m.group(1)
    return None


def option_texts(options):
    out = {}
    for o in options:
        m = re.match(r'^([A-Z])\.\s*(.*)$', o.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


# ------------------------------------------------------------------------------------------------ question parsing

def parse_vsi(q):
    """Named objects per VSI-Bench template."""
    t, s = q['question_type'], q['question']
    if t == 'object_counting':
        return {'cat': re.match(r'How many (.+?)\(s\) are in this room', s).group(1)}
    if t == 'object_abs_distance':
        m = re.search(r'distance between the (.+?) and the (.+?) \(in meters\)', s)
        return {'a': m.group(1), 'b': m.group(2)}
    if t == 'object_size_estimation':
        return {'a': re.search(r'dimension \(length, width, or height\) of the (.+?), measured', s).group(1)}
    if t == 'object_rel_distance':
        m = re.search(r'which of these objects \((.+?)\) is the closest to the (.+?)\?', s)
        return {'cands': [c.strip() for c in m.group(1).split(',')], 'target': m.group(2)}
    if t.startswith('object_rel_direction'):
        m = re.search(r'standing by the (.+?) and facing the (.+?), is the (.+?) to ', s)
        return {'stand': m.group(1), 'face': m.group(2), 'query': m.group(3)}
    if t == 'obj_appearance_order':
        m = re.search(r'in the video: (.+?)\?', s)
        return {'cats': [c.strip() for c in m.group(1).split(',')]}
    if t == 'route_planning':
        return parse_route(s)
    return {}


def _clean_obj(phrase):
    p = phrase.strip().rstrip('.').strip()
    p = re.sub(r'^(the|a|an)\s+', '', p, flags=re.I)
    return p


def parse_route(s):
    m = re.search(r'beginning at (?:the )?(.+?)(?:,)? (?:and )?facing (?:to |towards? )?(?:the )?(.+?)\. You want to navigate to (?:the )?(.+?)\. You will', s)
    start, face, goal = (_clean_obj(x) for x in m.groups())
    acts = s.split('):', 1)[1] if '):' in s else s
    acts = acts.split('You have reached')[0]
    steps = re.split(r'\s*\d+\.\s*', acts)
    plan = []
    for st in steps:
        st = st.strip().rstrip('.').strip()
        if not st:
            continue
        if 'please fill in' in st.lower():
            plan.append(('turn', None))
        else:
            mm = re.search(r'(?:Go|go) (?:forward|foward|straight) (?:until|to) (?:you reach )?(?:the )?(.+)$', st)
            if mm:
                plan.append(('go', _clean_obj(mm.group(1))))
            else:
                plan.append(('other', st))
    return {'start': start, 'face': face, 'goal': goal, 'plan': plan}


def to32(n, M):
    """'frame n of M' -> the nearest of the 32 uniformly sampled frames (M-frame and 32-frame samplings span the same video)."""
    return n if M == 32 else int(round((n - 1) * 31 / (M - 1))) + 1


def parse_vsti(q):
    P = _parse_vsti(q)
    for key in ('i', 'j', 'k'):
        if key in P and P.get('M', 32) != 32:
            P[key + '_raw'], P[key] = P[key], to32(P[key], P['M'])
    return P


def _parse_vsti(q):
    t, s = q['question_type'], q['question']
    if t == 'camera_displacement':
        m = re.search(r'between frame (\d+) and frame (\d+) of (\d+)', s)
        return {'i': int(m.group(1)), 'j': int(m.group(2)), 'M': int(m.group(3))}
    if t == 'camera_movement_direction':
        m = re.search(r'between frame (\d+) and frame (\d+) of (\d+)', s)
        return {'i': int(m.group(1)), 'j': int(m.group(2)), 'M': int(m.group(3))}
    if t == 'camera_obj_abs_dist':
        m = re.search(r'nearest point of the (.+?) in frame (\d+) of (\d+)', s)
        return {'obj': m.group(1), 'k': int(m.group(2)), 'M': int(m.group(3))}
    if t.startswith('camera_obj_rel_dist'):
        m = re.search(r'which of these objects \((.+?)\) is the closest to the camera in frame (\d+) of (\d+)', s)
        return {'cands': [c.strip() for c in m.group(1).split(',')], 'k': int(m.group(2)), 'M': int(m.group(3))}
    if t == 'obj_obj_relative_pos_lr':
        m = re.search(r'In frame (\d+) of (\d+), relative to (?:the )?(.+?), is (?:the )?(.+?) to the', s)
        return {'k': int(m.group(1)), 'M': int(m.group(2)), 'ref': m.group(3), 'a': m.group(4)}
    if t == 'obj_obj_relative_pos_ud':
        m = re.search(r'In frame (\d+) of (\d+), relative to (?:the )?(.+?), is (?:the )?(.+?) to the', s)
        return {'k': int(m.group(1)), 'M': int(m.group(2)), 'ref': m.group(3), 'a': m.group(4)}
    if t == 'obj_obj_relative_pos_nf':
        m = re.search(r'In frame (\d+) of (\d+), relative to the camera, is (?:the )?(.+?) \[Near/Far\] compared to (?:the )?(.+?)\?', s)
        return {'k': int(m.group(1)), 'M': int(m.group(2)), 'a': m.group(3), 'ref': m.group(4)}
    return {}


# ------------------------------------------------------------------------------------------------ geometry

def obb_points(obb, n=512, rng=None):
    """Uniform samples inside an OBB {centroid, axesLengths (full), normalizedAxes (rows = unit axes)}."""
    rng = rng if rng is not None else np.random.default_rng(0)
    c = np.asarray(obb['centroid'], float)
    half = np.asarray(obb['axesLengths'], float) / 2.0
    R = np.asarray(obb['normalizedAxes'], float).reshape(3, 3)
    u = rng.uniform(-1.0, 1.0, (n, 3)) * half
    return u @ R + c


def min_dist(P, Q):
    from scipy.spatial import cKDTree
    d, i = cKDTree(P).query(Q, k=1)
    j = int(np.argmin(d))
    return float(d[j]), P[int(i[j])], Q[j]


def obb_closest(obbs_a, obbs_b, n=512):
    rng = np.random.default_rng(0)
    best = None
    for a in obbs_a:
        for b in obbs_b:
            d = min_dist(obb_points(a, n, rng), obb_points(b, n, rng))[0]
            best = d if best is None or d < best else best
    return best


def point_obb_dist(p, obbs, n=4096):
    """Min distance from point p to points sampled inside the boxes (and exact for p inside)."""
    rng = np.random.default_rng(0)
    best = None
    for o in obbs:
        P = obb_points(o, n, rng)
        d = float(np.min(np.linalg.norm(P - np.asarray(p, float), axis=1)))
        best = d if best is None or d < best else best
    return best


def floor_angle(S, F, Q):
    """theta (deg) of Q seen from S facing F on the z-up floor plane; + is left."""
    u = np.asarray(F, float)[:2] - np.asarray(S, float)[:2]
    v = np.asarray(Q, float)[:2] - np.asarray(S, float)[:2]
    dot = u[0] * v[0] + u[1] * v[1]
    cross = u[0] * v[1] - u[1] * v[0]
    return math.degrees(math.atan2(cross, dot)), dot, cross


def direction_label(kind, theta):
    if kind == 'object_rel_direction_hard':
        return ('front' if abs(theta) < 90 else 'back') + '-' + ('left' if theta > 0 else 'right')
    if kind == 'object_rel_direction_medium':
        if abs(theta) >= 135:
            return 'back'
        return 'left' if theta > 0 else 'right'
    return 'left' if theta > 0 else 'right'


def turn_label(h, d, back=135.0):
    """'Turn Left/Right/Back' from heading h to direction d (2D, z-up floor)."""
    dot = h[0] * d[0] + h[1] * d[1]
    cross = h[0] * d[1] - h[1] * d[0]
    th = math.degrees(math.atan2(cross, dot))
    if abs(th) >= back:
        return 'Turn Back', th
    return ('Turn Left' if th > 0 else 'Turn Right'), th


# ------------------------------------------------------------------------------------------------ name matching
SYN = {'trash bin': ['trash can', 'trash bin', 'recycling bin', 'garbage bin', 'wastebasket', 'trash'],
       'tv': ['tv', 'television'], 'sofa': ['sofa', 'couch'], 'couch': ['couch', 'sofa'],
       'nightstand': ['nightstand', 'night stand', 'nightstand'], 'refrigerator': ['refrigerator', 'fridge', 'mini fridge'],
       'fridge': ['refrigerator', 'fridge'], 'wardrobe': ['wardrobe', 'wardrobe closet', 'closet', 'wardrobe cabinet'],
       'coat rack': ['coat rack', 'coat hanger'], 'stove': ['stove', 'gas stove', 'oven', 'stovetop'],
       'computer mouse': ['computer mouse', 'mouse'], 'table': ['table', 'desk', 'coffee table', 'dining table', 'end table'],
       'monitor': ['monitor', 'computer monitor', 'screen'], 'bookshelf': ['bookshelf', 'bookcase', 'shelf'],
       'door': ['door', 'doorframe', 'apartment door'], 'chair': ['chair', 'office chair', 'armchair']}
COLORS = r'\b(red|blue|green|yellow|white|black|brown|grey|gray|orange|pink|purple|wooden|small|large|big|tall|round|square)\b'


def head_noun(phrase):
    p = phrase.lower().strip().rstrip('.')
    p = re.sub(r'^(the|a|an)\s+', '', p)
    p = re.split(r'\s+(?:on|with|near|by|in|at|next to|under|above|beside|behind|of)\s+', p)[0]
    p = re.sub(COLORS, '', p)
    return re.sub(r'\s+', ' ', p).strip()


def match_labels(phrase, labels):
    """Labels (from a scene's full annotation) that the phrase refers to: exact head noun, synonyms, then substring."""
    h = head_noun(phrase)
    low = {l: l.lower() for l in labels}
    exact = [l for l, v in low.items() if v == h]
    if exact:
        return exact
    syn = SYN.get(h, [h])
    hits = [l for l, v in low.items() if v in syn]
    if hits:
        return hits
    hits = [l for l, v in low.items() if h in v or (len(v) > 3 and v in h)]
    return hits
