"""Classify every before/after admission change in the reviewer matrix."""
import json
from collections import Counter
from pathlib import Path
W = Path(__file__).resolve().parents[1]
b, a = [json.loads((W/'out'/f).read_text())['records'] for f in ('matrix_before2.json', 'matrix_after2.json')]
k = lambda r: (json.dumps(r['env'], sort_keys=True), r['host'], r['marker'], r['wrapper'])
old = {k(r): r for r in b}
assert len(old) == len(b) == len(a) == len({k(r) for r in a})
looser, stricter, wrapper_changes = Counter(), Counter(), []
for r in a:
    p = old[k(r)]; e = r['env']
    intended = (e.get('Q_E7') == '1' and e.get('STUDENT_R2_FRAME_HOST') != '1' and e.get('STUDENT_R2_LOCAL_NODE') != '1'
                and not r['host'].startswith('trinity'))
    for op in ('intake', 'materialize'):
        if r[op] and not p[op]:
            looser[(op, r['wrapper'], 'intended' if intended and (op == 'intake' or not r['marker']) else 'UNINTENDED')] += 1
        if p[op] and not r[op]:
            stricter[(op, r['wrapper'], 'Q_E7=%r native=%r' % (e.get('Q_E7'), e.get('STUDENT_R2_FRAME_HOST')))] += 1
        if intended and r['wrapper'] == 'direct' and not r[op] and not (op == 'materialize' and r['marker']):
            looser[(op, 'direct', 'INTENDED_BUT_REFUSED')] += 1
    if r['wrapper'] != 'direct' and (r['intake'], r['materialize'], r['resolved_native']) != (p['intake'], p['materialize'], p['resolved_native']):
        wrapper_changes.append(dict(key=k(r)))
    if r['wrapper'] != 'direct' and r['q_e7_present']:
        wrapper_changes.append(dict(key=k(r), q_e7_left=True))
summary = dict(looser={' | '.join(map(str, x)): n for x, n in looser.items()},
               stricter={' | '.join(map(str, x)): n for x, n in stricter.items()},
               wrapper_changes=wrapper_changes, cases=len(a))
(W/'out/MATRIX_DIFF.json').write_text(json.dumps(summary, indent=1)+'\n')
print(json.dumps(summary, indent=1))
