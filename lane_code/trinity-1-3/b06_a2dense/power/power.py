"""One-point power for card rule 3: room-bootstrap 95% half-width of the paired difference on the
450-item mean (main family: object_size_estimation, object_rel_distance, object_counting), using
the read kit's own f1f2.bootstrap (r5 room bootstrap, 10,000 replicates, seed 17).
Usage: power.py A544.jsonl [ITEMS_m200.jsonl] OUT.json  (without ITEMS: single-read proxy only)."""
import json, sys
sys.path.insert(0, '/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk')
import f1f2
TYPES = ('object_size_estimation', 'object_rel_distance', 'object_counting')
def sel(rows):
    return [r for r in rows if r['family'] == 'main' and r['task_type'] in TYPES]
args = sys.argv[1:]
a = sel(f1f2.load(args[0])); out = dict(types=TYPES, n_items=len(a), n_rooms=len({r['room'] for r in a}))
acc = f1f2.accuracy(a); out['a544_mean'] = acc
if len(args) == 3:
    b = sel(f1f2.load(args[1])); aa, bb = f1f2.align(a, b)
    keys = sorted(aa); d = f1f2.bootstrap([bb[k] for k in keys], [aa[k] for k in keys])
    lo, hi = d['ci95_pp']; out['paired_b_minus_a'] = d; out['half_width_pp'] = (hi - lo) / 2
    out['rule3_margin_ok'] = out['half_width_pp'] <= 1.0
else:
    lo, hi = acc['ci95_pct']; out['single_read_half_width_pct'] = (hi - lo) / 2
json.dump(out, open(args[-1], 'w'), indent=1, default=str); print(json.dumps(out, default=str)[:1500])
