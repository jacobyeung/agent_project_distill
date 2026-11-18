"""Merge sim_exec.py shards and compare with the archived pr_sim.py figures (POOLED_POWER_D0m200.json, pooled_item)."""
import glob, json, math
import numpy as np
F = sorted(glob.glob('sims/exec_seed4??.npz'))
res = np.concatenate([np.load(f)['res'] for f in F])
red = np.concatenate([np.load(f)['redrawn'] for f in F])
A = json.load(open('/scratch/jjyeung/orch_n30/pooled_rule/work/POOLED_POWER_D0m200.json'))['results']['pooled_item']
KEYS = ('no change (exchange)', 'a: size loss dev-S1 9.5 + R0-dev 4.3 (flips)', 'c: uniform loss 2 (flips)')
n = len(res)
out = dict(shards=F, pseudo_reads=n, redrawn_draws_total=int(red.sum()), pseudo_reads_with_a_redraw=int((red > 0).any(1).sum()), rows=[])
for c, k in enumerate(KEYS):
    for l, look in enumerate(('step200', 'later')):
        for e, ev in enumerate(('stop', 'H1', 'H2')):
            p = float(res[:, c, l, e].mean()); se = math.sqrt(max(p * (1 - p), 1e-12) / n)
            q, qse = A[look][k][ev]
            z = (p - q) / math.sqrt(se ** 2 + qse ** 2)
            out['rows'].append(dict(scenario=k, look=look, event=ev, executable=round(p, 4), executable_se=round(se, 4),
                                    archived=q, archived_se=qse, z=round(z, 2), within_2se=abs(z) <= 2))
json.dump(out, open('SIM_EXEC_AGREEMENT.json', 'w'), indent=1)
print('pseudo-reads', n, 'redrawn draws', out['redrawn_draws_total'], 'reads with a redraw', out['pseudo_reads_with_a_redraw'])
for r in out['rows']:
    print('%-48s %-8s %-5s exec %.4f (%.4f)  archived %.4f (%.4f)  z %+.2f %s' % (r['scenario'], r['look'], r['event'], r['executable'], r['executable_se'], r['archived'], r['archived_se'], r['z'], '' if r['within_2se'] else 'OUTSIDE 2 SE'))
# the unchanged model with the 3,000 extra null-only pseudo-reads (sim_exec.py ... null)
G = sorted(glob.glob('sims/null_seed5??.npz'))
nul = np.concatenate([res[:, 0]] + [np.load(f)['res'][:, 0] for f in G])
redn = int(red[:, 0].sum() + sum(np.load(f)['redrawn'][:, 0].sum() for f in G))
out['null_pooled'] = dict(shards=G, pseudo_reads=len(nul), redrawn_draws_total=redn, rows=[])
for l, look in enumerate(('step200', 'later')):
    for e, ev in enumerate(('stop', 'H1', 'H2')):
        p = float(nul[:, l, e].mean()); se = math.sqrt(max(p * (1 - p), 1e-12) / len(nul))
        q, qse = A[look][KEYS[0]][ev]
        z = (p - q) / math.sqrt(se ** 2 + qse ** 2)
        out['null_pooled']['rows'].append(dict(look=look, event=ev, executable=round(p, 4), executable_se=round(se, 4), archived=q, archived_se=qse,
                                               z=round(z, 2), within_2se=abs(z) <= 2))
        print('unchanged model, %d pseudo-reads %-8s %-5s exec %.4f (%.4f)  archived %.4f (%.4f)  z %+.2f %s' % (len(nul), look, ev, p, se, q, qse, z, '' if abs(z) <= 2 else 'OUTSIDE 2 SE'))
print('redrawn draws over all null pseudo-reads', redn)
json.dump(out, open('SIM_EXEC_AGREEMENT.json', 'w'), indent=1)
