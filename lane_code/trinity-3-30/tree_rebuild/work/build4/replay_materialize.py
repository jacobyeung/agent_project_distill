"""Reuse immutable row/clock envelopes; rerun the final producer to its RGB marker."""
import collections
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.r2_materialize import materialize
from student_pilot.p3_provenance import write
old=L/'work/build4/rows_complete'
out=L/'work/build4/rows_final_source';out.mkdir()
result=[]
for previous in json.loads((old/'RESULTS.json').read_text()):
    m=old/previous['group']/previous['family']/'manifest.json'
    dest=out/previous['group']/previous['family']
    report=materialize([m],dest,metadata_only=True,dense=False)
    rep=report['intake'][0]
    counts=list(rep['counts'].values())
    result.append({**previous,'seen':sum(c['seen'] for c in counts),'admitted':sum(c['admitted'] for c in counts),
        'refused':len(rep['refusals']),'reasons':dict(collections.Counter(r['reason'] for r in rep['refusals'])),
        'eval_rooms':sum('eval_rooms' in r['reason'] for r in rep['refusals']),
        'report':str((dest/'materialization.json').relative_to(L)),'status':report['status']})
write(out/'RESULTS.json',result)
print(json.dumps(dict(families=len(result),counts_equal=all(
    all(a[k]==b[k] for k in ('seen','admitted','refused','eval_rooms'))
    for a,b in zip(result,json.loads((old/'RESULTS.json').read_text()))))))
