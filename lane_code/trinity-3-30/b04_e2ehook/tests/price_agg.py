"""Paired room bootstrap of a pricing variant against `old` on dev-S1 (10,000 draws, seed 20261116, 95% percentile).
Usage: python -B price_agg.py PRICE.json VARIANT   (an unserved item scores 0)"""
import collections, json, sys
import numpy as np
p = json.load(open(sys.argv[1])); v = sys.argv[2]
rng = np.random.default_rng(20261116)
out = {}
for typ in sorted({r['type'] for r in p['rows']}):
    rows = [r for r in p['rows'] if r['type'] == typ]
    by = collections.defaultdict(list)
    for r in rows:
        by[r['room']].append((r['old'], r.get(v) or 0.))
    rooms = sorted(by)
    d = np.array([[sum(b - a for a, b in by[k]), len(by[k])] for k in rooms])
    draws = rng.integers(0, len(rooms), size=(10000, len(rooms)))
    boot = 100 * d[draws, 0].sum(1) / d[draws, 1].sum(1)
    out[typ] = dict(items=len(rows), rooms=len(rooms), old=100 * np.mean([r['old'] for r in rows]),
                    new=100 * np.mean([r.get(v) or 0. for r in rows]), diff=100 * d[:, 0].sum() / d[:, 1].sum(),
                    ci=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                    unserved=sum(r.get(v) is None for r in rows))
    print(f"{typ:28s} n={len(rows):3d} rooms={len(rooms):3d} old={out[typ]['old']:5.1f} {v}={out[typ]['new']:5.1f} "
          f"diff={out[typ]['diff']:+5.1f} [{out[typ]['ci'][0]:+5.1f},{out[typ]['ci'][1]:+5.1f}] unserved={out[typ]['unserved']}")
json.dump(out, open(sys.argv[1].replace('.json', f'_{v}_paired.json'), 'w'), indent=1)
