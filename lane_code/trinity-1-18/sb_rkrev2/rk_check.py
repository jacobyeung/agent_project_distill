"""Reviewer's independent CPU reproduction of the sb_rkfix S0/S1/S1b claims.

Uses only the deployed tree, the original K1 converter and stored local files; imports nothing from the kit's
adapter, harness or scripts. Writes only into this workspace.
"""
import glob, hashlib, importlib.util, json, math, random, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
KIT = Path('/scratch/jjyeung/orch_n30/sb_rkfix')
TREE = '/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872'
K1 = Path('/scratch/jjyeung/orch_n30/geo_k1')
K1M = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
R0 = Path('/scratch/jjyeung/orch_n30/b10_reserve')
CONVERT = K1 / 'k1towers/k1_convert.py'
sys.path.insert(0, TREE)
from student_pilot import camera_targets as ct
from student_pilot.ground_profiles import load_geometry
from student_pilot.scene_state import FrameMap
from trace_format import room_v314 as room
spec = importlib.util.spec_from_file_location('k1c_orig', CONVERT)
kc = importlib.util.module_from_spec(spec); spec.loader.exec_module(kc)
OUT = HERE / 'out'; OUT.mkdir(exist_ok=True)
report, ins = {}, {}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def rec(p):
    ins[str(p)] = sha(p); return ins[str(p)]


assert rec(Path(TREE) / 'trace_format/room_v314.py') == '37c8d5fcfa24bbc29155a18f4400ad91dd5326a22b019edd66809f192afd1d07'
assert rec(CONVERT).startswith('e2748156')


def load_pred(path):
    with np.load(path, allow_pickle=False) as z:
        p = {k: z[k] for k in z.files}
    grid = p['depth_grid64'] if 'depth_grid64' in p else p['depth_grid']
    slots = (p['anchor_slots'] if 'anchor_slots' in p else p['item_slots']).astype(int)
    return p, grid, slots


def geometry(path, scratch):
    p, grid, slots = load_pred(path)
    anchors = [int(x) for x in p['frame_indices'][slots]]
    C, _ = kc.native_cameras(p['c2w'][slots], ct)
    kc.write(Path(scratch), anchors, p['intrinsics'][slots].copy(), kc.canvas_affine(p['source_hw']), C,
             grid[slots].astype(np.float64), np.linspace(0, 1000, 51), 1.0, load_geometry, FrameMap)
    geo = load_geometry(scratch, FrameMap(tuple(anchors)), 'tower_scaled')
    assert geo.depth_scale_count == 1 and geo.pose_scale_count == 1
    return geo


def kernel(sample):
    try:
        return float(room.parse_response(room.format_result(room.from_points(**sample)))['area_m2'])
    except (ValueError, KeyError, FloatingPointError, np.linalg.LinAlgError):
        return None


def keep(sample, geo, test):
    pts = []
    for k, P in zip(sample['frames'], sample['points']):
        r = np.linalg.norm(P - np.asarray(geo.cam(k)[1], float), axis=1)
        pts.append(P[test(r)])
    return dict(sample, points=pts)


def area_set(path, train):
    out = {}
    try:
        geo = geometry(path, OUT / 'scratch_geom.npz')
    except ValueError as e:
        return {'R0': None, 'refused': str(e)}
    s = room.sample(geo, 'predicted')
    out['R0'] = kernel(s)
    if train:
        for pct, n in ((95, 'T05'), (90, 'T10'), (80, 'T20')):
            out[n] = kernel(keep(s, geo, lambda r, pct=pct: r <= np.percentile(r, pct)))
        for m in (4, 5, 6, 8):
            out['C%d' % m] = kernel(keep(s, geo, lambda r, m=m: r <= float(m)))
    return out


def mra(pred, gt):
    if pred is None or not math.isfinite(pred):
        return 0.0
    th = np.linspace(0.5, 0.95, 10)
    return float(np.mean(abs(pred - gt) / abs(gt) <= 1 - th))


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


# ---------------- S1b: 134 K1 room rows and 24 train-table entries ----------------
stored = {}
for f in sorted(glob.glob(str(K1 / 'harness/out_merged_mdp/*.json'))):
    rec(f)
    for it in json.load(open(f))['items']:
        if it['type'] == 'room_size_estimation' and it['arm'] == 'da3_native+R0':
            stored.setdefault(it['capture'], []).append(it)
by_capture = {}
for d in sorted(glob.glob(str(K1 / 'pred_gpu/da3/*/DONE.json'))):
    r = json.load(open(d)); by_capture.setdefault(r['capture'], []).append(Path(d).parent)
manifest = json.load(open(K1M)); rec(K1M)
split = {c['canonical']: c['k1_split'] for c in manifest['captures']}
rows = {}
for cap, items in sorted(stored.items()):
    assert len(by_capture[cap]) == 1, cap
    folder = by_capture[cap][0]; p = folder / 'pred.npz'
    assert json.load(open(folder / 'DONE.json'))['pred_sha256'] == rec(p)
    train = items[0]['split'] == 'train'
    assert {i['split'] for i in items} == {items[0]['split']} and split[cap] == items[0]['split']
    res = area_set(p, train)
    for it in items:
        rows[it['row_id']] = dict(it, **res)
ref = json.load(open(KIT / 'evidence/K1_RULE_VARIANTS.json')); rec(KIT / 'evidence/K1_RULE_VARIANTS.json')
order = [r['row_id'] for r in ref['rows']]
assert set(order) == set(rows)
equal = sum(1 for r in rows.values() if r['R0'] == r['pred'])
V = ('R0', 'T05', 'T10', 'T20', 'C4', 'C5', 'C6', 'C8')
variant_mismatch = [(r['row_id'], v) for r in ref['rows'] for v in V if rows[r['row_id']].get(v) != r[v]]
train_rows = [rows[i] for i in order if rows[i]['split'] == 'train']
for r in train_rows:
    for v in V:
        r.setdefault(v, None)
table, table_match = {}, 0
for ds in ('all', 'scannetpp', 'scannet'):
    s = [r for r in train_rows if ds in ('all', r['dataset'])]
    for v in V:
        m = boot([(r['room'], mra(r[v], r['gt'])) for r in s])
        dlt = boot([(r['room'], mra(r[v], r['gt']) - mra(r['R0'], r['gt'])) for r in s])
        rel = float(np.median([(r[v] - r['gt']) / r['gt'] for r in s if r[v] is not None]))
        e = ref['summary']['train'][ds + '/' + v]
        ok = (np.allclose(m, e['mra'], atol=1e-9) and np.allclose(dlt, e['minus_R0'], atol=1e-9)
              and abs(rel - e['median_rel']) < 1e-12 and len(s) == e['n'])
        table_match += ok
        table[ds + '/' + v] = dict(mra=m, minus_R0=dlt, median_rel=rel, n=len(s), matches_reference=ok)
report['S1b'] = dict(captures=len(stored), rows=len(rows), rebuilt_R0_equals_stored=equal,
                     train_rows=len(train_rows), heldout_rows=len(rows) - len(train_rows),
                     variant_cells_differing_from_reference=len(variant_mismatch),
                     train_table_entries=len(table), train_table_entries_matching=table_match,
                     heldout_variants_all_null=all(rows[i].get(v) is None for i in order if rows[i]['split'] != 'train' for v in V[1:]),
                     table=table)
print('S1b', {k: v for k, v in report['S1b'].items() if k != 'table'}, flush=True)

# ---------------- S1: kit CPU forwards vs stored GPU values ----------------
s1 = []
caps = {c['canonical']: c for c in manifest['captures']}
for cap, target in (('scannetpp/067e2e4e61', 14.73), ('scannetpp/036bce3393', 39.35)):
    c = caps[cap]; gpu_dir = by_capture[cap][0]
    gpu, ggrid, gslots = load_pred(gpu_dir / 'pred.npz')
    gdone = json.load(open(gpu_dir / 'DONE.json'))
    row = dict(capture=cap, stored_gpu_m2=target, stored_row=stored[cap][0]['pred'], label=stored[cap][0]['gt'],
               gpu_seconds=gdone.get('seconds'), gpu_peak_alloc_gib=gdone.get('peak_allocated_bytes', 0) / 2**30,
               gpu_peak_reserved_gib=gdone.get('peak_reserved_bytes', 0) / 2**30)
    for mode in ('k1_64', 'k1_32'):
        p = KIT / 'out/s1' / mode / cap.replace('/', '__') / 'pred.npz'
        done = json.load(open(p.parent / 'DONE.json'))
        assert done['pred_sha256'] == rec(p)
        cpu, cgrid, cslots = load_pred(p)
        dense = [int(f['index']) for f in c['dense_frames']]
        want_frames = dense if mode == 'k1_64' else list(c['anchor_indices'])
        assert cpu['frame_indices'].tolist() == want_frames
        assert cpu['frame_indices'][cslots].tolist() == list(c['anchor_indices'])
        a = kernel(room.sample(geometry(p, OUT / f'{mode}_{cap.split("/")[1]}.npz'), 'predicted'))
        g_anchor = ggrid[gslots]; c_anchor = cgrid[cslots]
        good = (g_anchor > 0) & (c_anchor > 0)
        row[mode] = dict(area_m2=a, seconds=done['seconds'], peak_rss_gib=done['peak_rss_kib'] / 2**20,
                         bytes_identical_to_gpu=sha(p) == sha(gpu_dir / 'pred.npz'),
                         median_abs_rel_depth_vs_gpu=float(np.median(np.abs(c_anchor[good] / g_anchor[good] - 1))),
                         max_abs_c2w_translation_diff=float(np.abs(cpu['c2w'][cslots][:, :3, 3] - gpu['c2w'][gslots][:, :3, 3]).max()))
    row['rel_err_64'] = abs(row['k1_64']['area_m2'] / target - 1)
    row['within_5pct'] = row['rel_err_64'] <= 0.05
    row['ratio_32_64'] = row['k1_32']['area_m2'] / row['k1_64']['area_m2']
    row['gpu_pred_area_own_code'] = kernel(room.sample(geometry(gpu_dir / 'pred.npz', OUT / 'gpu_tmp.npz'), 'predicted'))
    s1.append(row)
qs = sorted([q for q in map(json.loads, open(R0 / 'out/qsets/R0_QUESTIONS_rl_f32.jsonl')) if q['question_type'] == 'room_size_estimation'], key=lambda q: q['scene'])[:2]
rl = []
for q in qs:
    p = KIT / 'out/s1/r0_rl32' / q['scene'] / 'pred.npz'; rec(p)
    cpu, _, sl = load_pred(p)
    assert cpu['frame_indices'][sl].tolist() == q['frame_indices']
    geo = geometry(p, OUT / 'rl_tmp.npz'); s = room.sample(geo, 'predicted')
    rl.append(dict(scene=q['scene'], gt=q['gt']['area_m2'], R0=kernel(s), T10=kernel(keep(s, geo, lambda r: r <= np.percentile(r, 90)))))
report['S1'] = dict(k1=s1, r0_rl=rl)
print('S1', json.dumps(report['S1'], indent=1), flush=True)

# ---------------- S0 sample: R0-dev items, frames, layouts, baseline ----------------
qdev = R0 / 'out/qsets/R0_QUESTIONS_dev_f32.jsonl'
assert rec(qdev).startswith('b4e278f2') and ins[str(qdev)].endswith('a181')
assert sha(KIT / 'configs/R0_QUESTIONS_dev_f32.jsonl') == ins[str(qdev)]
qrl = R0 / 'out/qsets/R0_QUESTIONS_rl_f32.jsonl'
assert rec(qrl).startswith('5c4034f9') and ins[str(qrl)].endswith('d834')
dev = [q for q in map(json.loads, open(qdev)) if q['question_type'] == 'room_size_estimation']
km = json.load(open(KIT / 'configs/R0DEV_ROOM_MANIFEST.json'))['items']
kmi = {i['id']: i for i in km}
fm = json.load(open(R0 / 'out/FRAMES_MANIFEST.json'))
png_checked = png_bad = 0; layout_bad = []
for q in dev:
    union = sorted(set(q['frame_indices']) | set(np.floor(np.linspace(0, q['total_num_frames'] - 1, 64)).astype(int).tolist()))
    it = kmi[q['qid']]
    if it['frame_indices'] != q['frame_indices'] or it['union_indices'] != union or len(union) != 94 or it['scene'] != q['scene']:
        layout_bad.append(q['qid'])
    mp = R0 / 'out/frame_manifests' / f"{q['scene']}.json"
    assert sha(mp) == fm['scenes']['scannetpp/' + q['scene']]['manifest_sha256'] == it['frame_manifest_sha256']
    pins = json.load(open(mp))['frames']
    for i in union:
        h = sha(R0 / 'frames/scannetpp' / q['scene'] / f'{i:06d}.png'); png_checked += 1
        png_bad += (h != pins[str(i)] or h != it['frame_sha256'][str(i)])
direct = KIT / 'evidence/direct_m200_room134.json'
assert rec(direct) == 'c9b5994cc461420a0ccfb035cd252e27bac6da3016ab5d5a28f77a14239b319d'
drows = json.load(open(direct))['rows']
sets = {}
for r in drows:
    sets.setdefault(r['set'], []).append(r)
qgt = {q['qid']: q['gt']['area_m2'] for q in dev}
r0d = sets['R0-dev']
ft2 = 10.7639104167
gt_match = sum(1 for r in r0d if abs(r['gt'] / (ft2 if r['unit'] == 'ft2' else 1) - qgt[r['id']]) < 1e-6)
ledger = [l.split('  ', 1) for l in (KIT / 'review/LOCAL_INPUT_SHA256.txt').read_text().splitlines()]
rng = random.Random(7); sample_lines = rng.sample([l for l in ledger if not l[1].endswith('.png')], 300)
ledger_bad = [p for h, p in sample_lines if not Path(p).is_file() or sha(p) != h]
report['S0'] = dict(room_items=len(dev), unique_scenes=len({q['scene'] for q in dev}), kit_manifest_items=len(km),
                    ids_equal=set(kmi) == {q['qid'] for q in dev}, layout_mismatches=layout_bad,
                    pngs_hashed=png_checked, png_mismatches=png_bad,
                    ledger_sample=len(sample_lines), ledger_sample_bad=ledger_bad,
                    direct_sets={k: len(v) for k, v in sets.items()},
                    direct_ids_equal_question_ids=set(r['id'] for r in r0d) == set(qgt), direct_gt_equal_question_gt=gt_match,
                    direct_units={u: sum(r['unit'] == u for r in drows) for u in {r['unit'] for r in drows}},
                    direct_mra={k: 100 * float(np.mean([mra(r['direct'], r['gt']) for r in v])) for k, v in sets.items()},
                    cached_mra_equal=all(abs(mra(r['direct'], r['gt']) - r['direct_mra']) < 1e-12 for r in drows))
print('S0', json.dumps(report['S0'], indent=1), flush=True)
json.dump(dict(report=report, input_sha256=ins), open(OUT / 'RK_CHECK.json', 'w'), indent=1)
print('WROTE', OUT / 'RK_CHECK.json')
