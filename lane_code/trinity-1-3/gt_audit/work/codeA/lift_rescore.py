"""Re-aggregate the registered K1 lifting look (bestspread vs dep) with half-extent-corrected labels, agg.py unchanged."""
import glob, json, math, os, pathlib, subprocess, sys

LANE = pathlib.Path('/scratch/jjyeung/orch_n30/gt_audit')
H = LANE / 'work/k1b/orch_n30/b04host3/lift_price/harness'
LAB = {json.loads(l)['id']: json.loads(l) for l in open(LANE / 'work/k1audit/K1_LABELS_CORRECTED.jsonl')}


def mra(pred, truth):
    if pred is None or not math.isfinite(pred) or truth <= 0:
        return 0.0
    rel = abs(pred - truth) / abs(truth)
    return sum(rel < (100 - t) / 100 for t in range(50, 100, 5)) / 10


for variant in ['stored', 'corrected', 'drop']:
    d = LANE / 'work/lift' / variant; d.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(glob.glob(str(H / 'out_lift_heldout_reg/*.json'))):
        cap = json.load(open(p)); items = []
        for it in cap['items']:
            if it['type'] == 'object_abs_distance':
                lab = LAB[it['row_id']]
                assert abs(lab['stored'] - it['gt']) < 1e-9 and abs(mra(it['pred'], it['gt']) - it['mra']) < 1e-12
                if variant == 'corrected' and lab['convention'] == 'half':
                    it = dict(it, gt=lab['corrected'], mra=mra(it['pred'], lab['corrected'])); n += 1
                elif variant == 'drop' and lab['affected']:
                    n += 1; continue
            items.append(it)
        json.dump(dict(cap, items=items), open(d / os.path.basename(p), 'w'))
    r = subprocess.run([sys.executable, '-B', str(H / 'agg.py'), str(d), 'heldout', '-', 'S4+G1+dep,SO+G1+dep'], capture_output=True, text=True)
    open(LANE / 'work/lift' / ('AGG_HELDOUT_' + variant + '.txt'), 'w').write(r.stdout + r.stderr)
    print('==', variant, 'rows changed/dropped', n); print(r.stdout + r.stderr)
