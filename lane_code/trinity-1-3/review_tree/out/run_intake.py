import json, sys, collections, os
from pathlib import Path
W = Path('/scratch/jjyeung/orch_n30/review_tree/work')
sys.path.insert(0, str(W/'stage3/5c2ca33ca02a_t/o/ee000001'))
os.environ['STUDENT_R2_LOCAL_NODE'] = '1'
from student_pilot.r2_intake import intake
from student_pilot.r2_materialize import materialize
d = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
summary = {}
for m in sorted(d.glob('*.manifest.json')):
    adm, rep = intake(m, limit=2000)
    reasons = collections.Counter()
    for r in rep['refusals']:
        reasons[r['reason'][:110]] += 1
    seen = sum(c['seen'] for c in rep['counts'].values())
    summary[rep['family']] = dict(seen=seen, admitted=len(adm), refused=len(rep['refusals']), withheld=rep['rows_withheld'], reasons=dict(reasons.most_common(6)))
    print(rep['family'], 'seen', seen, 'admitted', len(adm), 'refused', len(rep['refusals']), 'withheld', rep['rows_withheld'])
    for k, v in reasons.most_common(4): print('    ', v, k)
json.dump(summary, open(out/'INTAKE_SUMMARY.json', 'w'), indent=1)
