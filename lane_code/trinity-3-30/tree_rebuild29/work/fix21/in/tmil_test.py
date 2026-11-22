"""fix21 T-mil tests: run the tree's own student_pilot.r1_training.validate on the kit config (k/c.json decoded)
with the milestone list varied. The pinned-file reads before line 98 are stubbed (init_policy, validate_binding, and
the mix card read), so line 98 and recipe_for run as in the tree. Usage: tmil_test.py <tree dir> <c.json decoded> <label>"""
import sys, json, copy
from pathlib import Path
TREE, CFG, LABEL = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(TREE))
import student_pilot.r1_training as R
import student_pilot.r1_persisted as RP, student_pilot.r1_coverage as RC
RP.init_policy = lambda value: None
RC.validate_binding = lambda cfg: None
base = json.loads(CFG.read_text())
scale = base['r1_training']['weight_scale']
R.pinned = lambda pin: pin
R.load = lambda pin: {'weight_scale': scale}
assert R.__file__.startswith(str(TREE))
cases = [('six', [100, 200, 400, 600, 800, 1000]), ('subset_100_200', [100, 200]), ('subset_400_1000', [400, 1000]),
         ('single_200', [200]), ('empty', []), ('outside_300', [100, 300]), ('outside_1200', [100, 1200]),
         ('wrong_order', [200, 100]), ('duplicate', [100, 100, 200])]
out = dict(tree=str(TREE), label=LABEL, results={})
for name, ms in cases:
    cfg = copy.deepcopy(base); cfg['milestones'] = list(ms); cfg['recipe']['milestones'] = list(ms)
    try:
        R.validate(cfg); r = 'PASS'
    except Exception as e:
        r = 'REFUSE ' + type(e).__name__ + ': ' + str(e)[:120]
    out['results'][name] = r
# Line 98 on its own: recipe_for stubbed to pass the list through unchanged (recipe_for's own check refuses
# wrong order and duplicates first in the real path).
import student_pilot.carrier_c1_sweep as S
real = S.recipe_for(base)
S.recipe_for = lambda cfg: {**real, 'milestones': cfg['milestones']}
out['line98_direct'] = {}
for name, ms in cases:
    cfg = copy.deepcopy(base); cfg['milestones'] = list(ms)
    try:
        R.validate(cfg); r = 'PASS'
    except Exception as e:
        r = 'REFUSE ' + type(e).__name__ + ': ' + str(e)[:120]
    out['line98_direct'][name] = r
print(json.dumps(out, indent=1))
