"""Reviewer's independent recompute of the kit's S1k kernel-constant selection on K1 train.

Own conversion (original k1_convert + deployed tree), own configurable kernel (the deployed room_v314.py with
the four constants substituted in its source text), labels and splits from the stored K1 harness output and
manifest. Imports nothing from the kit. Writes only into this workspace.
"""
import glob, hashlib, importlib.util, itertools, json, math, random, sys, types
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
KIT = Path('/scratch/jjyeung/orch_n30/sb_rkfix2')
TREE = '/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872'
K1 = Path('/scratch/jjyeung/orch_n30/geo_k1')
K1M = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
sys.path.insert(0, TREE)
from student_pilot import camera_targets as ct
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
spec = importlib.util.spec_from_file_location('k1c_orig', K1 / 'k1towers/k1_convert.py')
kc = importlib.util.module_from_spec(spec); spec.loader.exec_module(kc)
OUT = HERE / 'out'; OUT.mkdir(exist_ok=True)
ins = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def rec(p):
    ins[str(p)] = sha(p); return ins[str(p)]


ROOM = Path(TREE) / 'trace_format/room_v314.py'
assert rec(ROOM) == '37c8d5fcfa24bbc29155a18f4400ad91dd5326a22b019edd66809f192afd1d07'
src = ROOM.read_text()
for old, new in [("np.percentile(P[:, 2], 1) - .1)", "np.percentile(P[:, 2], 1) - HM)"),
                 ("else 2\n", "else MV\n"),
                 ("cell size 0.05 m; min frames {", "cell size {CELL_M:.2f} m; min frames {"),
                 ("cell size 0.05 m; min frames ([12])", "cell size ' + re.escape(f'{CELL_M:.2f}') + r' m; min frames ([12])")]:
    assert src.count(old) == 1, old
    src = src.replace(old, new)
room = types.ModuleType('room_cfg'); room.__file__ = str(ROOM)
exec(compile(src, str(ROOM), 'exec'), room.__dict__)


def setc(c):
    room.HM, room.MV, room.CELL_M, room.CLOSING_M = c['height_margin_m'], c['min_votes'], c['cell_m'], c['closing_m']


def kernel(sample):
    try:
        return float(room.parse_response(room.format_result(room.from_points(**sample)))['area_m2'])
    except (ValueError, KeyError, FloatingPointError, np.linalg.LinAlgError):
        return None


def geometry(path, scratch):
    with np.load(path, allow_pickle=False) as z:
        p = {k: z[k] for k in z.files}
    grid = p['depth_grid64'] if 'depth_grid64' in p else p['depth_grid']
    slots = (p['anchor_slots'] if 'anchor_slots' in p else p['item_slots']).astype(int)
    anchors = [int(x) for x in p['frame_indices'][slots]]
    C, _ = kc.native_cameras(p['c2w'][slots], ct)
    kc.write(Path(scratch), anchors, p['intrinsics'][slots].copy(), kc.canvas_affine(p['source_hw']), C,
             grid[slots].astype(np.float64), np.linspace(0, 1000, 51), 1.0, load_geometry, FrameMap)
    return load_geometry(scratch, FrameMap(tuple(anchors)), 'tower_scaled'), anchors


def mra(pred, gt):
    if pred is None or not math.isfinite(pred):
        return 0.0
    return float(np.mean(abs(pred - gt) / abs(gt) <= 1 - np.linspace(0.5, 0.95, 10)))


def boot(pairs, n=10000, seed=20261119):
    g = {}
    for k, v in pairs:
        g.setdefault(k, []).append(v)
    g = [(sum(v), len(v)) for v in g.values()]
    rng = random.Random(seed); s = []
    for _ in range(n):
        d = [g[rng.randrange(len(g))] for _ in g]
        s.append(sum(x[0] for x in d) / sum(x[1] for x in d))
    s.sort()
    return [100 * sum(x[0] for x in g) / sum(x[1] for x in g), 100 * s[int(.025 * n)], 100 * s[int(.975 * n)]]


manifest = json.load(open(K1M)); rec(K1M)
caps = {c['canonical']: c for c in manifest['captures']}
stored = {}
for f in sorted(glob.glob(str(K1 / 'harness/out_merged_mdp/*.json'))):
    rec(f)
    for it in json.load(open(f))['items']:
        if it['type'] == 'room_size_estimation' and it['arm'] == 'da3_native+R0' and it['split'] == 'train':
            stored.setdefault(it['capture'], []).append(it)
folder = {}
for d in sorted(glob.glob(str(K1 / 'pred_gpu/da3/*/DONE.json'))):
    folder.setdefault(json.load(open(d))['capture'], []).append(Path(d).parent)
grid = [dict(height_margin_m=a, cell_m=b, min_votes=c, closing_m=e)
        for a, b, c, e in itertools.product([.05, .10], [.05, .10], [1, 2], [.10, .20])]
OLD = dict(height_margin_m=.10, cell_m=.05, min_votes=2, closing_m=.20)
rows = []
for cap, items in sorted(stored.items()):
    assert caps[cap]['k1_split'] == 'train' and len(folder[cap]) == 1 and len(items) == 1, cap
    p = folder[cap][0] / 'pred.npz'
    assert json.load(open(folder[cap][0] / 'DONE.json'))['pred_sha256'] == rec(p)
    geo, anchors = geometry(p, OUT / 's1k_scratch.npz')
    assert anchors == list(caps[cap]['anchor_indices'])
    s = room.sample(geo, 'predicted')
    areas = []
    for c in grid:
        setc(c); areas.append(kernel(s))
    rows.append(dict(capture=cap, room=items[0]['room'], row_id=items[0]['row_id'], gt=items[0]['gt'],
                     stored_R0=items[0]['pred'], areas=areas))
kit = json.load(open(KIT / 'out/S1K_RESULTS.json')); rec(KIT / 'out/S1K_RESULTS.json')
reg = json.load(open(KIT / 'out/S1K_REGISTRATION.json')); rec(KIT / 'out/S1K_REGISTRATION.json')
kit_rows = {r['capture']: r for r in kit['result_table'][0]['rows']}
table = []
for i, c in enumerate(grid):
    kr = {r['capture']: r for r in kit['result_table'][i]['rows']}
    mean = 100 * float(np.mean([mra(r['areas'][i], r['gt']) for r in rows]))
    table.append(dict(constants=c, mra=mean, kit_mra=kit['result_table'][i]['mra'],
                      kit_constants_equal=kit['result_table'][i]['constants'] == c,
                      area_mismatches=sum(kr[r['capture']]['area_m2'] != r['areas'][i] for r in rows),
                      gt_mismatches=sum(kr[r['capture']]['gt'] != r['gt'] for r in rows)))
best = max(range(len(grid)), key=lambda i: table[i]['mra'])
iold = grid.index(OLD)
legacy_equals_stored = sum(r['areas'][iold] == r['stored_R0'] for r in rows)
gain = boot([(r['room'], mra(r['areas'][best], r['gt']) - mra(r['areas'][iold], r['gt'])) for r in rows])
res = dict(train_rows=len(rows), captures_equal_registration=sorted(r['capture'] for r in rows) == sorted(reg['captures']),
           grid_equals_registration=grid == reg['grid'], legacy_index=iold, legacy_rows_equal_stored_R0=legacy_equals_stored,
           my_winner_index=best, my_winner=grid[best], kit_winner_index=kit['winner_index'],
           ties_at_max=[i for i, t in enumerate(table) if t['mra'] == table[best]['mra']],
           max_abs_mra_diff_vs_kit=max(abs(t['mra'] - t['kit_mra']) for t in table),
           total_area_mismatches=sum(t['area_mismatches'] for t in table), total_gt_mismatches=sum(t['gt_mismatches'] for t in table),
           winner_minus_legacy_paired_boot=gain, table=table)
print(json.dumps({k: v for k, v in res.items() if k != 'table'}, indent=1))
json.dump(dict(result=res, input_sha256=ins), open(OUT / 'RK_S1K.json', 'w'), indent=1)
