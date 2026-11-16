"""Review K1C3: independent recompute of K1 table rows for every selected capture, and orientation stats.
usage: rev3_rows.py {primary|sensitivity} OUT.json [N_DIRECTION]"""
import json, sys, time, collections
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
WORK = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work')  # read-only import, run with -B
sys.path[:0] = [str(WORK), str(WORK / 'refit')]
import k1_pipeline as K
K._native()
B = K.B
import k1_guard as guard
import build_tables as T
import gt_set as G
from student_pilot import routed_features as F
guard.install()
O = Path('/scratch/jjyeung/orch_n30/k1_ops3/work')
which = sys.argv[1]; outp = Path(sys.argv[2]); ndir = int(sys.argv[3]) if len(sys.argv) > 3 else 0
sens = which == 'sensitivity'
gtfile = O / ('gt_sets/GT_SET_SENSITIVITY_300.json' if sens else 'gt_sets/GT_SET_PRIMARY_296.json')
tabroot = O / ('kc_guard_tests/patch4_sensitivity300/tables' if sens else 'kc_guard_tests/patch4_primary296/tables')
m = B.load(O / 'manifest_v2/a40fbc19.json')
selection = G.load(gtfile, sens); captures, meta = G.select(m, selection)
cache = Path('/scratch/jjyeung/k1/run_convert_2')
rec = json.loads((tabroot / 'TABLE_RECEIPT.json').read_text())
for n, pin in rec['files'].items():
    assert B.sha(pin['path']) == pin['sha256'], n
def by_scene(p):
    d = collections.defaultdict(list)
    for line in Path(p).read_text().splitlines():
        d[json.loads(line)['scene']].append(line)
    return d
cand_rows = by_scene(tabroot / 'candidates.jsonl'); pair_rows = by_scene(tabroot / 'pairs.jsonl')

def indep_map(lab):
    """Per-label union of routed_features.resize(lab==i) -- the deployed bool-mask rule."""
    out = np.full((lab.shape[0], 240, 320), np.iinfo(np.int64).min, np.int64)
    cover = np.zeros((lab.shape[0], 240, 320), np.int32)
    for f in range(lab.shape[0]):
        for i in np.unique(lab[f]):
            mk = F.resize(lab[f] == i, (240, 320))
            out[f][mk] = i; cover[f] += mk
    assert (cover == 1).all(), 'resize label masks do not partition the canvas'
    return out.astype(lab.dtype)

def best(mask, t, ids):
    return max((float((mask & (t == i)).sum()) / max(1., float((mask | (t == i)).sum())) for i in ids), default=0.)

res = dict(which=which, captures=0, identity=0, stretch=0, refused=[], mismatches=[], map_mismatch=[], vanished_any={}, vanished_named={}, direction={}, receipt_map_mismatch=[])
t0 = time.time(); ndone = 0
for c in captures:
    can = c['canonical']; res['captures'] += 1
    raw, geo, receipt = K.cached(c, cache / B.digest(can)[:16])
    with np.load(B.checked(selection['entries'][can]), allow_pickle=False) as z:
        lab = z['instances'] if 'instances' in z else z['inst']; fi = z['frame_indices']
    mine, kind = (lab, 'identity') if lab.shape[1:] == (240, 320) else (indep_map(lab), 'stretch_nearest_320x240_to_240x320')
    assert lab.shape[1:] in [(240, 320), (320, 240)], (can, lab.shape)
    theirs, tk = K.gt_canvas(lab)
    if tk != kind or theirs.dtype != mine.dtype or not np.array_equal(theirs, mine): res['map_mismatch'].append(can)
    if kind == 'identity': res['identity'] += 1; assert theirs is lab
    else:
        res['stretch'] += 1
        a = set(np.unique(lab).tolist()); b = set(np.unique(mine).tolist())
        if a - b: res['vanished_any'][can] = sorted(a - b)
        named = {i for ids in c['gt_name_ids'].values() for i in ids}
        if (a - b) & named: res['vanished_named'][can] = sorted((a - b) & named)
    if rec['gt_canvas_map'].get(can) != kind: res['receipt_map_mismatch'].append(can)
    if geo is None:
        res['refused'].append(can)
        if cand_rows.get(can) or pair_rows.get(can): res['mismatches'].append([can, 'refused capture has rows'])
        continue
    gt = dict(instances=mine, frame_indices=fi)
    with guard.capture(c):
        feats, g = T.extract(c, raw, geo)
        rows, pairs = T.label(c, feats, g, gt)
    a = [json.dumps(r) for r in rows]; b = [json.dumps(r) for r in pairs]
    if a != cand_rows.get(can, []) or b != pair_rows.get(can, []):
        res['mismatches'].append([can, len(a), len(cand_rows.get(can, [])), len(b), len(pair_rows.get(can, []))])
    if kind != 'identity' and len(res['direction']) < ndir:
        variants = dict(stretch=mine, stretch_flipud=mine[:, ::-1, :], stretch_fliplr=mine[:, :, ::-1],
                        rot90k1=np.rot90(lab, 1, axes=(1, 2)), rot90k3=np.rot90(lab, 3, axes=(1, 2)),
                        transpose=lab.transpose(0, 2, 1), transpose_flip=lab.transpose(0, 2, 1)[:, ::-1, ::-1])
        stats = {}
        for name, t in variants.items():
            vals = []
            for grp in feats.values():
                for cand in grp:
                    for frame, mask in cand['masks'].items():
                        tt = t[frame - 1]; vals.append(best(mask.astype(bool), tt, [i for i in np.unique(tt) if i >= 0]))
            v = np.array(vals); stats[name] = dict(n=len(v), mean=round(float(v.mean()), 4), frac05=round(float((v > .5).mean()), 4))
        res['direction'][can] = stats
    ndone += 1
    if ndone % 20 == 0: print(ndone, can, round(time.time() - t0), flush=True)
res['receipt_counts'] = rec['gt_canvas_map_counts']; res['receipt_refused'] = rec['geometry_refused']
res['receipt_captures'] = len(rec['gt_canvas_map']); res['selected'] = len(captures)
res['rows_total'] = [sum(map(len, cand_rows.values())), sum(map(len, pair_rows.values()))]
res['scenes_with_rows_not_selected'] = sorted(set(cand_rows) - {c['canonical'] for c in captures})
res['seconds'] = round(time.time() - t0)
outp.write_text(json.dumps(res, indent=1))
print(json.dumps({k: v for k, v in res.items() if k not in ('direction', 'vanished_any')}, indent=1))
