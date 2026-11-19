"""Compare strict MRA (analysis) with the official inclusive MRA (official.py official_mra) on
sb_scale2 DISTANCE_ROWS.json (all arms) and on step-544 displacement pairs (arm A), K1 train only."""
import os
for k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[k] = '8'
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, math
from collections import defaultdict
import numpy as np
import recompute as rc


def official_mra(pred, target, start=0.5, end=0.95, interval=0.05):
    if pred is None or target is None or not math.isfinite(pred) or not math.isfinite(target):
        return 0.0
    if target == 0.0:
        return 1.0 if pred == 0.0 else 0.0
    n = int((end - start) / interval + 2)
    cs = [start + i * (end - start) / (n - 1) for i in range(n)]
    rel = abs(pred - target) / abs(target)
    return sum(1.0 if rel <= (1.0 - c) else 0.0 for c in cs) / len(cs)


def main():
    out = dict(official_points=int((0.95 - 0.5) / 0.05 + 2))
    rows = json.load(open(rc.pin(rc.S2 / 'DISTANCE_ROWS.json')))['rows']
    diff = sum(1 for v in rows if abs(100 * official_mra(v['pred'], v['gt']) -
               rc.pair_mra([np.nan if v['pred'] is None else v['pred']], np.array([v['gt']]))[0]) > 1e-9)
    out['distance_rows'] = len(rows)
    out['distance_rows_strict_vs_official_differ'] = diff
    bars = json.load(open(rc.pin(rc.S1 / 'BARS_FROZEN.json')))
    n = nd = 0
    for r in bars['captures']:
        assert r['k1_split'] == 'train'
        if not r['gt_present']:
            continue
        with np.load(r['gt']['path']) as z:
            c2w, valid = z['c2w'], z['valid'].astype(bool)
        with np.load(r['tower']['path']) as z:
            raw_pose, dg, conf, slots = z['raw_pose'], z['depth_grid'].astype(float), z['depth_conf_grid'].astype(float), z['anchor_slots']
        with np.load(r['own544']['path']) as z:
            own = z['depth'].astype(float)
        scale, _ = rc.rule(dg, conf, own)
        cen = rc.centres(raw_pose[slots].astype(float))
        i, j = np.triu_indices(32, 1)
        truth = np.linalg.norm(c2w[i, :3, 3] - c2w[j, :3, 3], axis=1)
        ok = valid[i] & valid[j] & np.isfinite(truth) & (truth >= 0.1)
        pred = np.linalg.norm(cen[i] - cen[j], axis=1)[ok] * scale
        truth = truth[ok]
        strict = rc.pair_mra(pred, truth)
        off = np.array([100 * official_mra(float(p), float(g)) for p, g in zip(pred, truth)])
        n += len(truth)
        nd += int(np.sum(np.abs(strict - off) > 1e-9))
    out['displacement_pairs'] = n
    out['displacement_pairs_strict_vs_official_differ'] = nd
    out['input_sha256'] = rc.PINS
    out['code_sha256'] = rc.sha(__file__)
    out['command'] = 'cd /scratch/jjyeung/orch_n30/sb_scalerev && env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python work/mra_check.py'
    (rc.Path(__file__).resolve().parent / 'MRA_CHECK.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k != 'input_sha256'}, indent=1))


if __name__ == '__main__':
    main()
