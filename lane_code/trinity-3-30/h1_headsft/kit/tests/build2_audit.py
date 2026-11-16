"""Bounded source, input and printed-gap audit; retains every output in K."""
import ast
import hashlib
import json
import tarfile
from pathlib import Path
from h1eval.items import K, sha, pin, R0, DIRECT, TASKS, REVSI, read_items, load_manifest
from rows.expected_calls import expected_calls

files=set(K.joinpath('h1eval').rglob('*.py'))
files.update(K.joinpath('tests').glob('*.py'));files.update(K.joinpath('rows').glob('*.py'))
files.update(K/'tree/student_pilot'/p for p in ('carrier_c1.py','carrier_c1_run.py','carrier_c1_routing.py','h1.py','h1_faithful.py','h1_r0.py'))
for p in files:ast.parse(p.read_text(),filename=str(p))
checks=json.loads((K/'READER_BUILD2_INPUT_SHA256.json').read_text())
for c in checks:assert sha(K/c['destination'])==c['sha256'],c['destination']
manifest=load_manifest(K/'items/revsi999.json')
assert manifest['count']==999 and manifest['r0_check']['found']==0
from tests.test_eval import call_outputs
from h1eval.scorers import printed,usage
base,_=call_outputs();changed,_=call_outputs({'name':'scale_scene','k':2})
a,b=printed(base['calls'][-1])['distance'],printed(changed['calls'][-1])['distance']
base['text']=f'<answer>{a}</answer>';changed['text']=f'<answer>{b}</answer>'
gap=dict(baseline_gap_m=a,perturbed_gap_m=b,relative_printed_change=abs(b-a)/abs(a),
         usage=usage(base,changed,dict(question='Distance between the chair and the table (in meters)?',question_type='object_abs_distance')))
assert gap['usage']['follow']==1 and gap['relative_printed_change']>=.20
(K/'logs/gap_acceptance_build2.json').write_text(json.dumps(gap,indent=2)+'\n')
archive=Path('/scratch/jjyeung/orch_n30/b07_offread/in/c8r/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kit_combo3.tar.gz')
with tarfile.open(archive) as t:
    operands={r['id']:r['operands'] for line in t.extractfile('kit_combo3/out/ITEMS.jsonl')
              if (r:=json.loads(line))['question_type']=='object_abs_distance'}
matched=0
for r in read_items(TASKS):
    if r['question_type']=='object_abs_distance':
        a,b=operands[r['id']]
        expected=[f'<ground obj="{a}" mode="box">',f'<ground obj="{b}" mode="box">',f'<gap a="{a}" b="{b}" rule="box_grid_5cm">']
        assert expected_calls(r['question'],r['question_type'])==expected,(r['id'],r['question'])
        matched+=1
parsed=sum(bool(expected_calls(r['question'],r['question_type'])) for r in read_items(REVSI) if r['question_type']=='object_abs_distance')
assert (matched,parsed)==(150,283)
report=dict(syntax_pass_count=len(files),reader_copies_verified=len(checks),gap_acceptance=True,
            native_distance_calls_matched=matched,revsi_distance_calls_parsed=parsed,
            bytes=sum(p.stat().st_size for p in K.rglob('*') if p.is_file()))
assert report['bytes']<1500000000
(K/'logs/build2_audit.json').write_text(json.dumps(report,indent=2)+'\n')
inputs=[pin(p) for p in (R0,R0.parent/'R0_DEV_ROOMS.txt',DIRECT,TASKS,REVSI,archive,
                       Path('/scratch/jjyeung/orch_n30/b04_e2ehook/tests/test_tiny_e2e.py'))]
inputs.append(json.loads((K/'items_sources/c8r_inventory.json').read_text())['source'])
(K/'BUILD2_INPUT_SHA256.json').write_text(json.dumps(inputs,indent=2)+'\n')
print(json.dumps(report));print(json.dumps(gap))
