"""Synthetic tests of k5s.auc and k5s.boot_auc."""
import importlib.util, sys
spec = importlib.util.spec_from_file_location('k5s', '/scratch/jjyeung/orch_n30/lever7/k5s/k5s.py')
k = importlib.util.module_from_spec(spec); spec.loader.exec_module(k)
ok = True
def check(name, cond):
    global ok; ok &= bool(cond); print(('PASS ' if cond else 'FAIL ')+name)
pos, neg = [5, 6, 7, 8, 9], [1, 2, 3]
check('perfect separation auc == 1.0', k.auc(pos, neg) == 1.0)
check('reversed auc == 0.0', k.auc(neg, pos) == 0.0)
check('all ties auc == 0.5', k.auc([1, 1], [1, 1, 1]) == 0.5)
check('half tie case auc == 0.75', k.auc([2], [1, 2]) == 0.75)
b = k.boot_auc(pos, neg); print(b)
check('perfect separation bootstrap ci == [1, 1]', b['auc'] == 1.0 and b['ci95'] == [1.0, 1.0] and b['defined_draws'] + b['undefined_draws'] == 10000)
b = k.boot_auc(neg, pos); print(b)
check('reversed bootstrap ci == [0, 0]', b['auc'] == 0.0 and b['ci95'] == [0.0, 0.0])
b1, b2 = k.boot_auc([1, 3, 5, 2], [2, 4, 0]), k.boot_auc([1, 3, 5, 2], [2, 4, 0])
check('bootstrap deterministic under seed 0', b1 == b2 and b1['ci95'][0] <= b1['auc'] <= b1['ci95'][1])
check('empty class gives None', k.boot_auc([], [1])['auc'] is None and k.auc([1], []) is None)
check('klass rule', k.klass(dict(rotation_max_deg=61, accepted=False)) == 'gross' and k.klass(dict(rotation_max_deg=4, accepted=True)) == 'pass' and k.klass(dict(rotation_max_deg=30, accepted=False)) == 'moderate')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
