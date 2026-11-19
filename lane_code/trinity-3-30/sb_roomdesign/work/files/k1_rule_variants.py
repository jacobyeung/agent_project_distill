"""Design-time check on K1 (CPU, no GPU, no new tower pass): rebuild lane b14's da3_native room areas from its
stored DA3 predictions, confirm they equal the stored per-item values, and price fixed-math variants of the
room rule on K1 TRAIN rows only (T05/T10/T20: drop each frame's farthest 5/10/20% of points by range; C4..C8: drop
points farther than 4..8 m from their camera). Held-out rows are rebuilt for rule R0 alone (their R0 values are already known).
One scratch geometry file (SCRATCH_NPZ) is overwritten per capture and left in place.

Usage: python k1_rule_variants.py MIRROR_TAR MERGED_DIR TREE K1_CONVERT_PY SCRATCH_NPZ OUT_JSON
"""
import importlib.util, io, json, os, random, sys, tarfile
from pathlib import Path
import numpy as np

tar_path, merged, tree, convert_py, scratch_npz, out_json = sys.argv[1:7]
sys.path.insert(0, tree)
from student_pilot import camera_targets as ct
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
from trace_format import room_v314 as room
spec = importlib.util.spec_from_file_location('k1_convert', convert_py)
kc = importlib.util.module_from_spec(spec); spec.loader.exec_module(kc)

stored = {}
for name in sorted(os.listdir(merged)):
    for it in json.load(open(os.path.join(merged, name)))['items']:
        if it['type'] == 'room_size_estimation' and it['arm'] == 'da3_native+R0':
            stored.setdefault(it['capture'], []).append(it)
print('captures with room rows', len(stored), 'rows', sum(len(v) for v in stored.values()), flush=True)

def trimmed(sample, geo, pct):
    pts = []
    for k, P in zip(sample['frames'], sample['points']):
        centre = np.asarray(geo.cam(k)[1], float)
        r = np.linalg.norm(P - centre, axis=1)
        pts.append(P[r <= np.percentile(r, pct)])
    return dict(sample, points=pts)

def cut(sample, geo, metres):
    pts = []
    for k, P in zip(sample['frames'], sample['points']):
        r = np.linalg.norm(P - np.asarray(geo.cam(k)[1], float), axis=1)
        pts.append(P[r <= metres])
    return dict(sample, points=pts)

def area(kernel_sample):
    try:
        res = room.from_points(**kernel_sample)
        return float(room.parse_response(room.format_result(res))['area_m2'])
    except (ValueError, KeyError, FloatingPointError, np.linalg.LinAlgError):
        return None

VARIANTS = ('R0', 'T05', 'T10', 'T20', 'C4', 'C5', 'C6', 'C8')
rows, pending = [], {}
with tarfile.open(tar_path) as tar:
    for m in tar:
        if not m.name.startswith('geo_k1/pred_gpu/da3/') or not m.isfile():
            continue
        folder, leaf = m.name.rsplit('/', 1)
        if leaf == 'DONE.json':
            pending.setdefault(folder, {})['cap'] = json.load(tar.extractfile(m))['capture']
        elif leaf == 'pred.npz':
            pending.setdefault(folder, {})['npz'] = tar.extractfile(m).read()
        entry = pending.get(folder, {})
        if 'cap' not in entry or 'npz' not in entry:
            continue
        cap = entry['cap']; del pending[folder]
        if cap not in stored:
            continue
        with np.load(io.BytesIO(entry['npz']), allow_pickle=False) as z:
            pred = {k: z[k] for k in z.files}
        slots = pred['anchor_slots'].astype(int)
        anchors = [int(x) for x in pred['frame_indices'][slots]]
        result = {}
        try:
            C, up = kc.native_cameras(pred['c2w'][slots], ct)
            kc.write(Path(scratch_npz), anchors, pred['intrinsics'][slots].copy(), kc.canvas_affine(pred['source_hw']), C,
                     pred['depth_grid64'][slots].astype(np.float64), np.linspace(0, 1000, 51), 1.0, load_geometry, FrameMap)
            geo = load_geometry(scratch_npz, FrameMap(tuple(anchors)), 'tower_scaled')
            sample = room.sample(geo, 'predicted')
            result['R0'] = area(sample)
            if stored[cap][0]['split'] == 'train':
                for pct, name in ((95, 'T05'), (90, 'T10'), (80, 'T20')):
                    result[name] = area(trimmed(sample, geo, pct))
                for metres in (4, 5, 6, 8):
                    result['C%d' % metres] = area(cut(sample, geo, float(metres)))
        except (ValueError, AssertionError) as exc:
            result = {'R0': None, 'refused': type(exc).__name__ + ':' + str(exc)}
        for it in stored[cap]:
            rows.append(dict(row_id=it['row_id'], capture=cap, room=it['room'], split=it['split'], dataset=it['dataset'],
                             gt=it['gt'], stored_R0=it['pred'], **{k: result.get(k) for k in VARIANTS}, refused=result.get('refused')))
        if len(rows) % 20 == 0:
            print('rows', len(rows), flush=True)

def mra(pred, gt):
    if pred is None:
        return 0.0
    rel = abs(pred - gt) / abs(gt)
    conf = [0.5 + i * 0.45 / 9 for i in range(10)]
    return sum(1.0 if rel <= 1.0 - c else 0.0 for c in conf) / 10

def boot(pairs, n=10000, seed=20261119):
    groups = {}
    for room_key, v in pairs:
        groups.setdefault(room_key, []).append(v)
    g = [(sum(v), len(v)) for v in groups.values()]
    rng, s = random.Random(seed), []
    for _ in range(n):
        d = [g[rng.randrange(len(g))] for _ in g]
        s.append(sum(x[0] for x in d) / sum(x[1] for x in d))
    s.sort()
    return [100 * sum(x[0] for x in g) / sum(x[1] for x in g), 100 * s[int(.025 * n)], 100 * s[int(.975 * n)]]

def equal(r):
    a, b = r['R0'], r['stored_R0']
    return a == b or (a is not None and b is not None and abs(a - b) < 0.005)

same = sum(1 for r in rows if equal(r))
print('R0 rebuilt equals stored on %d of %d rows' % (same, len(rows)))
for r in rows:
    if not equal(r):
        print('  differs', r['capture'], r['R0'], r['stored_R0'], r['refused'])
summary = dict(rebuilt_equals_stored=[same, len(rows)], train={})
train = [r for r in rows if r['split'] == 'train']
print('K1 TRAIN, da3_native geometry; MRA [95% room bootstrap]; paired minus R0; median signed error')
for ds in ('all', 'scannetpp', 'scannet'):
    s = [r for r in train if ds in ('all', r['dataset'])]
    for v in VARIANTS:
        m = boot([(r['room'], mra(r[v], r['gt'])) for r in s])
        d = boot([(r['room'], mra(r[v], r['gt']) - mra(r['R0'], r['gt'])) for r in s])
        rel = [(r[v] - r['gt']) / r['gt'] for r in s if r[v] is not None]
        summary['train'][ds + '/' + v] = dict(mra=m, minus_R0=d, median_rel=float(np.median(rel)), n=len(s))
        print('%-9s %-4s n %3d  %6.2f [%5.1f, %5.1f]  minus R0 %+6.2f [%+6.2f, %+6.2f]  median rel %+.3f' % (ds, v, len(s), m[0], m[1], m[2], d[0], d[1], d[2], float(np.median(rel))))
json.dump(dict(summary=summary, rows=rows), open(out_json, 'w'), indent=1)
