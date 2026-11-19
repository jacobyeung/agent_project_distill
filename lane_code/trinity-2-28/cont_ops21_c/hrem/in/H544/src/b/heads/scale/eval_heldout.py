"""Held-out report for a trained ScaleHead (run once, after training; nothing here feeds back into training).

(a) per-capture s/SO within [0.8, 1.2] vs E3's S2/S4; (b) quick-path distance MRA:
pred_SH = pred_SO+G1 * s_SH / SO per row (approximation; E3 measured near-linear distance in s),
paired room bootstrap (10,000 draws, seed 20261116) vs S4+G1 and SO+G1/SO+GO.
Usage: python -I eval_heldout.py HEAD_DIR OUT_JSON [SCALES_JSON_OUT]
"""
import glob, hashlib, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import torch
from scale_head import load_head, prepare_inputs

E3_HO = '/scratch/jjyeung/orch_n30/b04_e2ehook/work/e3/work/harness/out_ho'
TOWERS = '/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2'


def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, allow_nan=False).encode()).hexdigest()


def mra(pred, truth):  # identical to E3 harness.mra
    if pred is None or not math.isfinite(pred) or truth <= 0:
        return 0.0
    rel = abs(pred - truth) / abs(truth)
    return sum(rel < (100 - t) / 100 for t in range(50, 100, 5)) / 10


def boot_table(rows_by_arm, arms, refs):
    base = rows_by_arm[arms[0]]
    ids = sorted(base)
    clusters = sorted({base[i]['room'] for i in ids})
    cidx = {c: k for k, c in enumerate(clusters)}
    cl = np.array([cidx[base[i]['room']] for i in ids])
    nc = len(clusters)
    rng = np.random.default_rng(20261116)
    draws = rng.integers(0, nc, size=(10000, nc))
    W = np.stack([np.bincount(d, minlength=nc) for d in draws]).astype(float)
    cnt = np.bincount(cl, minlength=nc)

    def boot(v):
        s = np.bincount(cl, weights=v, minlength=nc)
        m = (W @ s) / (W @ cnt)
        return [100 * v.mean(), 100 * np.percentile(m, 2.5), 100 * np.percentile(m, 97.5)]

    vals = {a: np.array([rows_by_arm[a][i]['mra'] if i in rows_by_arm[a] else 0. for i in ids]) for a in arms}
    out = dict(n_items=len(ids), n_rooms=nc, arms={})
    for a in arms:
        out['arms'][a] = dict(mra=boot(vals[a]), refusals=sum(1 for i in ids if rows_by_arm[a].get(i, {}).get('pred') is None),
                              paired={r: boot(vals[a] - vals[r]) for r in refs if r != a and r in vals})
    return out


def main():
    head_dir, out_json = sys.argv[1], sys.argv[2]
    torch.set_num_threads(8)
    head = load_head(head_dir)
    caps, items = [], []
    for p in sorted(glob.glob(E3_HO + '/*__*.json')):
        d = json.load(open(p))
        g = d['diagnostics']
        assert g['split'] == 'heldout'
        with torch.no_grad():
            s = float(torch.exp(head(**prepare_inputs(f"{TOWERS}/{digest(g['capture'])[:16]}/tower.npz")))[0])
        caps.append(dict(capture=g['capture'], room=g['room'], dataset=g['dataset'], SO=g['SO'], SH=s,
                         S2=g['scales']['S2'] if g.get('scales') else None, S4=g['scales']['S4'] if g.get('scales') else None,
                         geometry_refused=g.get('refused')))
        items += [dict(r, s_SH=s, SO=g['SO'], s_S4=(g.get('scales') or {}).get('S4')) for r in d['items']]
    # (a) scale accuracy
    def w20(key, subset):
        v = np.array([c[key] / c['SO'] if c[key] is not None and np.isfinite(c[key]) else np.nan for c in subset])
        ok = (v >= .8) & (v <= 1.2)
        return dict(n=len(subset), within20=float(np.mean(ok)), mean_abs_log=float(np.nanmean(np.abs(np.log(v)))))
    finite = [c for c in caps if not c['geometry_refused']]
    scale = {k: dict(all57=w20(k, caps), e3_finite53=w20(k, finite)) for k in ('SH', 'S2', 'S4')}
    # (b) quick-path distance
    dist = [r for r in items if r['type'] == 'object_abs_distance']
    by = {}
    for r in dist:
        by.setdefault(r['arm'], {})[r['row_id']] = r
    for name, key in (('SH+G1~quick', 's_SH'), ('S4+G1~quick', 's_S4')):
        by[name] = {}
        for i, r in by['SO+G1'].items():
            s = r[key]
            pred = None if r['pred'] is None or s is None else r['pred'] * s / r['SO']
            by[name][i] = dict(r, arm=name, pred=pred, mra=mra(pred, r['gt']))
    arms = ['SH+G1~quick', 'S4+G1~quick', 'S4+G1', 'S2+G1', 'SO+G1', 'SO+GO', 'GT']
    table = boot_table(by, arms, ['S4+G1', 'SO+G1', 'SO+GO'])
    res = dict(head_dir=head_dir, weights_sha256=json.load(open(os.path.join(head_dir, 'scale_head.json')))['weights_sha256'],
               scale=scale, distance_quick=table, per_capture=caps,
               note='SH+G1~quick and S4+G1~quick scale the SO+G1 row prediction by s/SO; S4+G1 is E3\'s exact run.')
    json.dump(res, open(out_json, 'w'), indent=1)
    if len(sys.argv) > 3:
        json.dump({c['capture']: c['SH'] for c in caps}, open(sys.argv[3], 'w'), indent=1)
    for k, v in scale.items():
        print('scale', k, v)
    print(f"distance items={table['n_items']} rooms={table['n_rooms']}")
    for a, v in table['arms'].items():
        print(f"{a:14s} {v['mra'][0]:5.1f} [{v['mra'][1]:5.1f},{v['mra'][2]:5.1f}] ref={v['refusals']} "
              + ' '.join(f"| vs {r}: {d[0]:+5.1f} [{d[1]:+5.1f},{d[2]:+5.1f}]" for r, d in v['paired'].items()))


if __name__ == '__main__':
    main()
