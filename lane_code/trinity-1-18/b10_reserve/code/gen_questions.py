"""Frame-tied GT questions for one R0 capture (ScanNet++), ReVSI/VSI-Bench types, D0 v5 wording.

Every item carries answers for both layouts (32 and 64 frames): an object counts as seen in a layout when it covers
>= VIS_MIN_PX raster pixels in at least one shown frame. Objects named in an item must be seen in BOTH layouts; counts
and appearance orders are labelled per layout (answer_f32, answer_f64).
Units follow the benchmark: counts (integer), object size (cm, integer), absolute distance (m, 2 decimals), room size
(m^2, 2 decimals). Multiple-choice options are shuffled by a hash of the qid.
usage: gen_questions.py SCENE_DIR SPLIT CAP_MULT OUT.jsonl  (CAP_MULT scales per-type caps; 1 for R0-dev)
"""
import hashlib, itertools, json, math, os, sys
import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r0lib  # noqa: E402

GEN_VERSION = 'r0gen-v1'
CAPS = dict(object_counting=3, object_counting_multi=1, object_size_estimation=3, object_abs_distance=3,
            object_rel_distance=3, object_rel_direction_easy=2, object_rel_direction_medium=2,
            object_rel_direction_hard=2, obj_appearance_order=2, room_size_estimation=1)
NOTE_MED = 'An object is to my back if I would have to turn at least 135 degrees in order to face it.'
NOTE_HARD = 'The directions refer to the quadrants of a Cartesian plane (if I am standing at the origin and facing along the positive y-axis).'
MIN_VERTS = 20


def h(*a):
    return hashlib.sha256('|'.join(map(str, a)).encode()).hexdigest()


class Rng:
    def __init__(self, *seed):
        self.r = np.random.default_rng(int(h(*seed)[:16], 16))

    def pick(self, seq, k):
        seq = list(seq)
        return [seq[i] for i in self.r.permutation(len(seq))[:k]]


def mc(qid, correct, distract):
    opts = [correct] + list(distract)
    perm = np.random.default_rng(int(h('opts', qid)[:16], 16)).permutation(len(opts))
    letters = 'ABCD'
    shown = [opts[i] for i in perm]
    return ['%s. %s' % (letters[i], o) for i, o in enumerate(shown)], letters[shown.index(correct)]


def minbox(P):
    xy = P[:, :2] - P[:, :2].mean(0)
    best = None
    for a in np.deg2rad(np.arange(0, 90, 1.0)):
        c, s = math.cos(a), math.sin(a)
        q = xy @ np.array([[c, -s], [s, c]])
        ext = q.max(0) - q.min(0)
        if best is None or ext[0] * ext[1] < best[0]:
            best = (ext[0] * ext[1], ext)
    return [float(best[1][0]), float(best[1][1]), float(P[:, 2].max() - P[:, 2].min())]


def room_area(V, cell=0.1):
    ij = np.floor((V[:, :2] - V[:, :2].min(0)) / cell).astype(int)
    g = np.zeros(ij.max(0) + 1, bool); g[ij[:, 0], ij[:, 1]] = True
    g = ndimage.binary_closing(g, structure=np.ones((3, 3)), iterations=2)
    g = ndimage.binary_fill_holes(g)
    return float(g.sum() * cell * cell)


def angle(a, b, c, away=False):
    """Signed angle (deg) of C seen from A when facing B (or facing away from B); + = left (counter-clockwise)."""
    f = (b - a)[:2]; f = -f if away else f
    t = (c - a)[:2]
    return math.degrees(math.atan2(f[0] * t[1] - f[1] * t[0], f @ t))


def main(sdir, split, mult, out):
    scene_id = os.path.basename(os.path.normpath(sdir))
    S = r0lib.load_scene(sdir)
    total, cams, conv = r0lib.load_cameras(sdir)
    lay = {n: r0lib.layout(total, n) for n in (32, 64)}
    vis = {n: r0lib.visible_counts(S, cams, lay[n]) for n in lay}
    inst = S['inst']
    keep = [k for k, it in enumerate(inst) if it['label'] not in r0lib.STRUCT and len(it['v']) >= MIN_VERTS
            and not any(w in it['label'] for w in ('wall', 'floor', 'ceiling'))]
    by_label = {}
    for k in keep:
        by_label.setdefault(inst[k]['label'], []).append(k)
    seen, first = {}, {}
    for n in lay:
        seen[n], first[n] = set(), {}
        for pos, fi in enumerate(lay[n]):
            for k, c in vis[n][fi].items():
                if c >= r0lib.VIS_MIN_PX:
                    seen[n].add(k); first[n].setdefault(k, pos + 1)
    uniq = sorted(l for l, ks in by_label.items() if len(ks) == 1 and ks[0] in seen[32] and ks[0] in seen[64])
    U = {l: by_label[l][0] for l in uniq}
    P = {l: S['V'][inst[U[l]]['v']] for l in uniq}
    C = {l: P[l].mean(0) for l in uniq}
    trees = {l: cKDTree(P[l]) for l in uniq}

    def dist(a, b):
        return float(trees[a].query(P[b], k=1)[0].min())

    caps = {k: v * mult for k, v in CAPS.items()}
    items = []
    base = dict(dataset='scannetpp', scene=scene_id, r0_split=split, total_num_frames=total, fps=60.0,
                frame_indices_f32=lay[32], frame_indices_f64=lay[64], gen_version=GEN_VERSION)

    def add(qt, sub, q, opts, a32, a64, unit, info):
        qid = 'r0_' + h(GEN_VERSION, scene_id, qt, sub, q)[:20]
        if opts is not None:
            opts, a32 = mc(qid, a32, opts)
            a64 = a32 if a64 == 'same' else a64
        items.append(dict(base, qid=qid, question_type=qt, subtype=sub, question=q, options=opts or [],
                          answer_f32=a32, answer_f64=a64, unit=unit, gt=info))

    R = Rng(GEN_VERSION, scene_id)
    # counting (single category): frame-tied count per layout; at least 2 seen in the 32-frame layout
    cands = [l for l, ks in sorted(by_label.items()) if sum(k in seen[32] for k in ks) >= 2 and len(ks) <= 20]
    for l in R.pick(cands, caps['object_counting']):
        ks = by_label[l]
        add('object_counting', 'single', 'How many %s(s) do we have in this room?' % l, None,
            str(sum(k in seen[32] for k in ks)), str(sum(k in seen[64] for k in ks)), 'count',
            dict(category=l, scene_instances=len(ks), ids=[inst[k]['id'] for k in ks]))
    multi = [l for l, ks in sorted(by_label.items()) if any(k in seen[32] for k in ks) and len(ks) <= 20]
    for _ in range(caps['object_counting_multi']):
        if len(multi) < 2:
            break
        ls = sorted(R.pick(multi, 2))
        c32 = sum(k in seen[32] for l in ls for k in by_label[l]); c64 = sum(k in seen[64] for l in ls for k in by_label[l])
        add('object_counting', 'multiple', 'How many objects are there altogether among the %s(s) and %s(s) in this room?' % tuple(ls),
            None, str(c32), str(c64), 'count', dict(categories=ls))
    for l in R.pick(uniq, caps['object_size_estimation']):
        dims = minbox(P[l]); cm = int(round(max(dims) * 100))
        if cm < 5:
            continue
        add('object_size_estimation', 'longest_dimension',
            'What is the length of the longest dimension (length, width, or height) of the %s, measured in centimeters?' % l,
            None, str(cm), str(cm), 'cm', dict(category=l, box_dims_m=dims, box_rule='min-area z-up box of instance mesh vertices'))
    pairs = [p for p in itertools.combinations(uniq, 2)]
    for a, b in R.pick(pairs, caps['object_abs_distance'] * 3):
        if sum(i['question_type'] == 'object_abs_distance' for i in items) >= caps['object_abs_distance']:
            break
        d = dist(a, b)
        if d < 0.2:
            continue
        add('object_abs_distance', 'closest_point',
            'Measuring from the closest point of each object, what is the distance between the %s and the %s (in meters)?' % (a, b),
            None, '%.2f' % d, '%.2f' % d, 'm', dict(pair=[a, b], distance_m=d))
    if caps['room_size_estimation']:
        A = room_area(S['V'])
        add('room_size_estimation', 'floor_area',
            'What is the size of this room (in square meters)? \nIf multiple rooms are shown, estimate the size of the combined space.',
            None, '%.2f' % A, '%.2f' % A, 'm2', dict(area_m2=A, rule='xy occupancy of all mesh vertices, 0.1 m cells, closing x2, hole fill'))
    for mode in ('closest', 'farthest'):
        n_ok = 0
        for t in R.pick(uniq, 20):
            if n_ok >= max(1, caps['object_rel_distance'] // 2 + (mode == 'closest')):
                break
            others = [l for l in uniq if l != t]
            if len(others) < 4:
                break
            opts = R.pick(others, 4)
            ds = sorted(((dist(t, o), o) for o in opts), reverse=(mode == 'farthest'))
            gap = abs(ds[1][0] - ds[0][0])
            if gap < 0.2 or gap < 0.15 * max(ds[0][0], ds[1][0]):
                continue
            q = ('Measuring from the closest point of each object, which of these objects (%s) is the %s the %s?'
                 % (', '.join(sorted(opts)), 'closest to' if mode == 'closest' else 'farthest from', t))
            add('object_rel_distance', mode, q, [o for _, o in ds[1:]], ds[0][1], 'same', 'choice',
                dict(target=t, distances_m={o: d for d, o in ds}))
            n_ok += 1
    trip = list(itertools.permutations(uniq, 3))
    for sub in ('easy', 'medium', 'hard'):
        qt = 'object_rel_direction_' + sub; n_ok = 0
        for a, b, c in R.pick(trip, 200):
            if n_ok >= caps[qt]:
                break
            if np.linalg.norm((C[b] - C[a])[:2]) < 0.6 or np.linalg.norm((C[c] - C[a])[:2]) < 0.6:
                continue
            away = R.r.random() < 0.35
            th = angle(C[a], C[b], C[c], away)
            face = ('facing away from the %s' % b) if away else ('facing the %s' % b)
            stem = 'If I am standing by the %s and %s, ' % (a, face)
            if sub == 'easy':
                if abs(th) < 15 or abs(th) > 165:
                    continue
                ans = 'left' if th > 0 else 'right'
                q = stem + ('is the %s to my left or to my right?' % c if away else 'is the %s to the left or the right of the %s?' % (c, b))
                add(qt, 'away' if away else 'toward', q, ['right' if ans == 'left' else 'left'], ans, 'same', 'choice',
                    dict(standing=a, facing=b, query=c, away=away, angle_deg=th))
            elif sub == 'medium':
                if min(abs(abs(th) - 135), abs(th)) < 15:
                    continue
                ans = 'back' if abs(th) >= 135 else ('left' if th > 0 else 'right')
                q = stem + 'is the %s to my left, right, or back?\n%s' % (c, NOTE_MED)
                add(qt, 'away' if away else 'toward', q, [x for x in ('left', 'right', 'back') if x != ans], ans, 'same', 'choice',
                    dict(standing=a, facing=b, query=c, away=away, angle_deg=th))
            else:
                if min(abs(th), abs(abs(th) - 90), 180 - abs(th)) < 15:
                    continue
                ans = ('front-' if abs(th) < 90 else 'back-') + ('left' if th > 0 else 'right')
                q = stem + 'is the %s to my front-left, front-right, back-left, or back-right?\n%s' % (c, NOTE_HARD)
                add(qt, 'away' if away else 'toward', q, [x for x in ('front-left', 'front-right', 'back-left', 'back-right') if x != ans],
                    ans, 'same', 'choice', dict(standing=a, facing=b, query=c, away=away, angle_deg=th))
            n_ok += 1
    n_ok = 0
    for _ in range(30):
        if n_ok >= caps['obj_appearance_order'] or len(uniq) < 4:
            break
        ls = R.pick(uniq, 4)
        f32 = [first[32][U[l]] for l in ls]; f64 = [first[64][U[l]] for l in ls]
        if len(set(f32)) < 4 or len(set(f64)) < 4:
            continue
        o32 = [l for _, l in sorted(zip(f32, ls))]; o64 = [l for _, l in sorted(zip(f64, ls))]
        if o32 != o64:
            continue
        dis = []
        for perm in R.pick(list(itertools.permutations(o32)), 24):
            if list(perm) != o32 and ', '.join(perm) not in dis:
                dis.append(', '.join(perm))
            if len(dis) == 3:
                break
        q = 'What will be the first-time appearance order of the following categories in the video: %s?' % ', '.join(sorted(ls))
        add('obj_appearance_order', 'first_seen', q, dis, ', '.join(o32), 'same', 'choice',
            dict(first_pos_f32=dict(zip(ls, f32)), first_pos_f64=dict(zip(ls, f64))))
        n_ok += 1
    fz = [np.median(S['V'][it['v'], 2]) for it in inst if it['label'] == 'floor']
    cz = [np.median(S['V'][it['v'], 2]) for it in inst if it['label'] == 'ceiling']
    zup = dict(floor_z=float(np.median(fz)) if fz else None, ceiling_z=float(np.median(cz)) if cz else None,
               z_p02=float(np.percentile(S['V'][:, 2], 2)), z_p98=float(np.percentile(S['V'][:, 2], 98)))
    meta = dict(zup=zup, scene=scene_id, total_frames=total, camera=conv, instances=len(inst), kept=len(keep), unique_seen=len(uniq),
                seen_f32=len(seen[32]), seen_f64=len(seen[64]), items=len(items), gen_version=GEN_VERSION)
    with open(out, 'w') as f:
        for it in items:
            f.write(json.dumps(it, sort_keys=True) + '\n')
    print(json.dumps(meta))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4])
