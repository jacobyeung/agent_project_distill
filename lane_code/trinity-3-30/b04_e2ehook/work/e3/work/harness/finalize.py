"""Finish the integrated run's summary after its end-of-run sanity test hit refused captures (no GT-floor field)."""
import sys, json
sys.path.insert(0, '/scratch/jjyeung/orch_n30/e3_geom/work/harness')
import importlib.util as iu
sp = iu.spec_from_file_location('e3h', '/scratch/jjyeung/orch_n30/e3_geom/work/harness/harness.py'); H = iu.module_from_spec(sp); sp.loader.exec_module(H)
rows = [json.loads(l) for l in open(H.OUT / 'PER_ITEM.jsonl')]
caps = [json.loads(l) for l in open(H.OUT / 'PER_CAPTURE.jsonl')]
fits = json.load(open(H.OUT / 'FITS.json'))
inv = json.load(open(H.OUT / 'INVENTORY.json'))
ok = [c for c in caps if 'gt_floor_at_low_z' in c]
H.log_test('GT_low_z_floor_sanity', all(c['gt_floor_at_low_z'] for c in ok), n_checked=len(ok),
           n_refused_G1_unchecked=len(caps) - len(ok), failed_captures=[c['capture'] for c in ok if not c['gt_floor_at_low_z']])
for typ, arm, expected in [('object_abs_distance', 'GT', 82), ('room_size_estimation', 'GT+R0', 99)]:
    sel = [r for r in rows if r['split'] == 'train' and r['type'] == typ and r['arm'] == arm]
    mean = 100 * sum(r['mra'] for r in sel) / len(sel)
    H.log_test('GT_ceiling_' + typ, mean >= expected - 10, train_mra=mean, n_items=len(sel), reference_expectation=expected)
summary = H.summarise(rows, [dict(c, gt_floor_at_low_z=c.get('gt_floor_at_low_z', True)) for c in caps], fits, inv, 'specified')  # refused captures unchecked; see GT_low_z_floor_sanity
H.dump(H.OUT / 'SUMMARY.json', summary)
H.report(summary)
print('FINALIZED')
