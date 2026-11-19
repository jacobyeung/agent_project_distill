from pathlib import Path
import json,sys,ast,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build19';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import load,file_pin
out={}
for step in (400,600):
    root=B/'proofs/native'/str(step);v=load(root/'q/RESULT.json')
    assert v['refusal']=='ValueError:R1_POST_FILTER_CAPACITY_SHORTFALL:pose'
    assert any(e['function']=='student_pilot.s1_admission.admit' and e['result']=='PASS' for e in v['stage_events'])
    prepared=[]
    for p in (root/'q/p').rglob('prepared/receipt.json'):
        r=load(p)
        if r.get('component_evidence'):
            assert len(r['component_evidence'])==9 and all(x['status']=='DEFERRED' for x in r['component_evidence'].values())
            prepared.append(dict(receipt=file_pin(p),slots=r['component_evidence'],counts={k:s['count'] for k,s in r['streams'].items()}))
    assert prepared
    twins=load(root/'TWINS.json');assert 'Missing component evidence: init_m544' in twins['non_R1']['refusal']
    out[str(step)]=dict(status=v['status'],refusal=v['refusal'],events=v['stage_events'],preparations=prepared,twins={k:x.get('refusal') for k,x in twins.items()},first_batches='NOT EXECUTED: population refused')
O=B/'proofs/native_summary';O.mkdir(exist_ok=True)
(O/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n')
(B/'STATUS.md').write_text('Build 19: GO=false. Both milestones pass native preparation with nine recorded DEFERRED slots, then refuse at r1_population.bind_prepared: R1_POST_FILTER_CAPACITY_SHORTFALL:pose. All-rank losses are not executed. Tests, mutations, final suites and packaging are in progress.\n')
print('Both native preparations passed; both populations refused capacity.')
