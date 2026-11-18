"""Refuse a missing answer form and preserve a selected init pin in staging metadata."""
import json,os,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix';T=L/'work/tree_r1';O=B/'proofs/mix_edges'
O.mkdir(exist_ok=True);sys.path[:0]=[str(T),str(B)]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot import r2_mix
from student_pilot.p3_provenance import load,file_pin
from launch_r2.build import build,verify
from tests.test_r2_build import inputs
from tests.test_r2_build7 import settings
from tests.r2_init_fixture import PIN,INIT
def reject(fn,reason):
    try:fn()
    except ValueError as error:assert reason in str(error),str(error)
    else:raise AssertionError(reason)
reject(lambda:r2_mix.table(both_path={'minority_count':0}),'Pinned minority count')
mix=O/'mix.json';mix.write_text(json.dumps(r2_mix.table(both_path={'minority_count':1})))
qid=load(B/'proofs/r1_edges/admitted_identity.json')['examples'][0]['qid']
row=next(r for r in load(B/'proofs/extent_admission/units/samples.json') if r['qid']==qid)
item=dict(row=row,stream='routing',mix_cell={'type':'units'})
reject(lambda:r2_mix.reindex([item],dict(mix_pin=file_pin(mix),artifact_heads=['pose','depth']),O/'index'),
       'rows_lane_missing_minority_form')
value=load(B/'KIT_RESULT.json')['a0']['launch_inputs']
value['init']=dict(artifact_id='synthetic_boundary',sha256=INIT['artifact_sha256'],
                  location=str(O/'unavailable_pretrained_input'),selected_by='NEXT_LEG_INIT_RULE_20261116')
kit=O/'kit'
if kit.exists() and not (kit/'BUILD.json').exists():
    retained=O/'partial';assert not retained.exists();kit.rename(retained)
if kit.exists():
    result=load(kit/'BUILD.json');verify(kit)
else:
    result=build(L/'fixtures/work/kit07ca49df_meta/m',kit,connector='none',records=inputs(),init_pin=PIN,launch_inputs=value)
    assert result['kit_sha256']==verify(kit)
cfg=load(kit/result['config']['path']);launch=load(kit/'k/launch.json')
# Scan the small capsules for the actual normal staging-plan entry.
found=[]
for path in (kit/'k').glob('*.json'):
    data=load(path)
    if isinstance(data,dict) and 'entries' in data:
        entry=data['entries'].get(cfg['init_artifact']['artifact']['path'])
        if entry and entry.get('parts')==[value['init']['location']]:found.append(entry)
assert len(found)==1 and found[0]['sha256']==INIT['artifact_sha256']
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',init_entry=found[0],kit_sha256=result['kit_sha256'],
    minority_refusal='PASS',source_qid=qid,GO=False,
    scope='Real admitted-row metadata and normal kit builder/reader. The pretrained input location is a synthetic unresolved boundary parameter; no weights copied or input availability claimed.'),indent=2)+'\n')
monitor.save(O);print('PASS')
