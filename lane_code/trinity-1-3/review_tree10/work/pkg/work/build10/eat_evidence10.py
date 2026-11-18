from pathlib import Path
from collections import Counter
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
summary=json.loads((B/'EAT1_SUMMARY.json').read_text());result={}
def group(r):
    f=r.get('file','');fn=r.get('function','');text=r.get('text','')
    if 'g3t' in f or 'vggt' in f:return 'G6'
    if 'point_depth_head' in f or ('carrier_c1_routing' in f and ('click' in fn or 'STENCIL' in text)):return 'G1'
    if 'carrier_c1_routing' in f and any(x in fn for x in ('wrap','pose','turn')):return 'G2'
    if 'contracts.py' in f and 'heading_available' in fn:return 'G3'
    if any(x in f for x in ('decoupled_v.py','ground_context.py','calculator.py')):return 'G4'
    if 'carrier_c1_batch_decode.py' in f and any(x in text for x in ('max_call','MAX_CALL','budget')):return 'G5'
    if r.get('rule','').startswith('A4') or any(x in f for x in ('box_v313','ground_v313')):return 'G7'
    return 'Other / expanded v7 scope'
for name,value in summary.items():
    report=json.loads(Path(value['source']).read_text());groups={}
    for clause in ('A3','A4'):
        for offender in report['clauses'].get(clause,{}).get('offenders',[]):
            g=group(offender);groups.setdefault(g,[]).append(dict(clause=clause,**offender))
    row=dict(source=value['source'],groups=groups,counts={g:dict(Counter(r['clause'] for r in rows)) for g,rows in groups.items()})
    if not name.endswith('_before'):
        items=[json.loads(line) for line in (B/'proofs/eat1'/name/'run/ITEMS.jsonl').read_text().splitlines()]
        row['items']=[dict(id=v['id'],error=v.get('error'),calls=len((v.get('output') or {}).get('calls',[]))) for v in items]
        row['errors']=dict(Counter(v['error'].splitlines()[-1] for v in items if v.get('error')))
        row['A5']=report['clauses']['A5']
    result[name]=row
(B/'EAT1_GROUP_EVIDENCE.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:dict(counts=v['counts'],errors=v.get('errors')) for k,v in result.items()},indent=2))
