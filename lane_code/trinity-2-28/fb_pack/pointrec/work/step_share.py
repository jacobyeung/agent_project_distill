"""Step-level language-loss coefficient shares from probe.json and the final-mode configs.

Run: bash work/run.sh step_share   (after probe; writes work/step_share.json)
A row's LM component is mean(CE * w) (carrier_c1.py:543-548), so its coefficient mass is mean(w): 2.0 for a
pointing row under pointing_weights row_mean 2, 1.0 for VQA/routing rows. Each microstep is divided by
len(plan) (carrier_c1_run.py:1587); stream weights come from recipe.weights. Pose and MDG rows carry no LM tokens.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
TREE = Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1')
sys.path.insert(0, str(TREE))
from student_pilot.r1_training import STREAMS  # noqa: E402

def sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


INPUTS = [HERE/'probe.json', TREE/'configs/E2E-1C.json', TREE/'configs/E2E-1G.json', TREE/'student_pilot/r1_training.py',
          Path(__file__)]
probe = json.loads((HERE/'probe.json').read_text())
counts = probe['row_counts']
frac = {k: v / sum(counts.values()) for k, v in counts.items()}
stats = probe['stats']


def mix_mean(key):
    return sum(frac[k] * stats[key][k]['mean'] for k in frac)


per_row = dict(
    base_weighted=dict(coef=2.0, think=mix_mean('base_think_over_n')),
    base_uniform=dict(coef=1.0, think=mix_mean('base_think_share_uniform')),
    locate_weighted=dict(coef=2.0, think=2.0 * mix_mean('locate_think_share')))
out = dict(inputs={str(p): sha(p) for p in INPUTS}, visible_null_fraction=frac, per_pointing_row=per_row, mixes={})
budgets = {}
for name in ('E2E-1C.json', 'E2E-1G.json'):
    cfg = json.loads((TREE/'configs'/name).read_text())
    budgets[name] = (cfg['recipe']['stream_rows_per_step'], cfg['recipe']['weights'], len(cfg['recipe']['mix']))
budgets['r1_training.STREAMS'] = (dict(STREAMS), dict(vqa=1.0, routing=1.0, pointing=1.0), None)
for name, (rows, weights, microsteps) in budgets.items():
    entry = dict(rows_per_step=rows, microsteps=microsteps, total_rows=sum(rows.values()),
                 pointing_row_share_all=rows['pointing'] / sum(rows.values()))
    lm_rows = sum(rows[s] for s in ('vqa', 'routing', 'pointing'))
    entry['pointing_row_share_lm_rows'] = rows['pointing'] / lm_rows
    for arm, value in per_row.items():
        mass_other = sum(rows[s] * weights.get(s, 0.) for s in ('vqa', 'routing'))
        mass_point = rows['pointing'] * weights['pointing'] * value['coef']
        think = rows['pointing'] * weights['pointing'] * value['think']
        entry[arm] = dict(pointing_share_of_lm_coefficient=mass_point / (mass_point + mass_other),
                          think_share_of_lm_coefficient=think / (mass_point + mass_other))
    out['mixes'][name] = entry
(HERE/'step_share.json').write_text(json.dumps(out, indent=1) + '\n')
print(json.dumps(out, indent=1))
