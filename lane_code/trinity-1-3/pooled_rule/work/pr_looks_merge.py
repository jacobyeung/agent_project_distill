"""Merge pr_looks.py: probability that an unchanged model is stopped at look 1 (step-200 levels), by look 2, by look 3
(later-look levels), and the bound for four looks (three looks jointly plus the fourth look's own rate)."""
import glob, json, math
import numpy as np
F = sorted(glob.glob('looks_seed*.npz'))
Z = [np.load(f) for f in F]
cat = lambda k: np.concatenate([z[k] for z in Z])
ub, mub, sub, smub = cat('ub'), cat('mub'), cat('sub'), cat('smub')


def rate(x):
    p = float(np.mean(x))
    return [round(p, 4), round(math.sqrt(max(p * (1 - p), 1e-12) / len(x)), 4)]


out = dict(files=F, pseudo_legs=len(ub))
for name, U, M in (('pooled_rule', ub, mub), ('devS1_rule', sub, smub)):
    first = (U[:, 0, :, 0] < 0).any(1) | (M[:, 0, 0] < 0)                       # look 1 at the step-200 levels
    later = [(U[:, j, :, 1] < 0).any(1) | (M[:, j, 1] < 0) for j in range(3)]    # each look at the later-look levels
    s2, s3 = first | later[1], first | later[1] | later[2]
    single_later = float(np.mean([x.mean() for x in later]))
    r = dict(look1_step200_levels=rate(first), single_look_at_later_levels=[rate(x) for x in later],
             by_look2=rate(s2), by_look3=rate(s3),
             four_looks_upper_estimate=round(rate(s3)[0] + single_later, 4),
             sum_of_single_looks=round(rate(first)[0] + 3 * single_later, 4),
             H1_look1=rate((U[:, 0, :, 0] < 0).any(1)), H2_look1=rate(M[:, 0, 0] < 0))
    out[name] = r
json.dump(out, open('LOOKS.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
