"""Exercise the real stdlib equality gate; all constructed proofs are TEST ONLY."""
import copy,hashlib,importlib.util,json,sys,tempfile
from pathlib import Path
H=Path(__file__).resolve().parents[1];sys.path.insert(0,str(H/'tools'))
import derive_kit_h1 as dk
out=Path(tempfile.mkdtemp(prefix='guard_',dir=H/'evidence/fix7_selection'))
final=json.loads((H/'build/over_local.json').read_text());dk.validate_selection_equality(final)
base=json.loads((H/'evidence/fix8_before/build/over_local.json').read_text());passed=[]
for n in ('4.json','review.json','staging.json'):base['add_k'][n]['path']=str(H/'evidence/fix8_before/payload'/n)
def refused(value,message):
 try:dk.validate_selection_equality(value)
 except (ValueError,KeyError) as exc:
  assert message in str(exc),(message,str(exc));passed.append(message)
 else:raise AssertionError('accepted invalid equality evidence')
dk.validate_selection_equality(base)
for status in ('READY','PREPARATION_ONLY'):
 stale=copy.deepcopy(base);stale['status']=status;refused(stale,'stale selection')
# A fixture manufactures this pair to test validation only; it is never deployed.
candidate=json.loads((H/'payload/d_f232d4160d75b582.json').read_text())
candidate['implementation']=json.loads((H/'evidence/fix7_selection/implementation.json').read_text())
cp=out/'TEST_ONLY_SELECTION.json';dk.write(cp,candidate);pin=dict(path=str(cp),sha256=dk.sha(cp))
over=copy.deepcopy(base);over['add_k'].pop('pool_selection_aa128e6f.json')
over['add_k']['pool_selection_7test.json']=pin
over['config']['s1_routing']['selection']=dict(path=dk.KIT_LOGICAL+'pool_selection_7test.json',sha256=pin['sha256'])
refused(over,'requires a pinned equality report')
report=dict(schema='selection-equality-v1',status='EQUAL',regenerated=True,
 reference_sha256=dk.SELECTION_REFERENCE,raw_reference_sha256=dk.SELECTION_RAW_REFERENCE,
 selection_sha256=pin['sha256'],content_sha256=dk.SELECTION_CONTENT,raw_content_sha256=dk.SELECTION_RAW_CONTENT,
 implementation_sha256=dk.SELECTION_IMPLEMENTATION,tree_sha256=json.loads((H/'payload/7.json').read_text())['tree_sha256'],
 code_sha256=dk.sha(H/'payload/7.json'),tool_sha256=dk.SELECTION_TOOL,differences=[],raw_differences=[],
 fields={k:True for k in candidate if k!='implementation'},indices=dk.SELECTION_INDICES,
 inputs={h:dict(path='/fixture/'+h,bytes=n) for h,n in dk.SELECTION_INPUT_SIZES.items()},production_authorized=False)
def bind(value,tag):
 p=out/(tag+'.json');dk.write(p,value);proof=dict(path=str(p),sha256=dk.sha(p))
 v=copy.deepcopy(over);v['selection_equality']=proof;v['add_k']['selection_equality.json']=proof
 return v
valid=bind(report,'TEST_ONLY_REPORT');dk.validate_selection_equality(valid);passed.append('matched pair accepted')
# Exercise the actual derive entry point: the report guard must precede source IO.
try:dk.derive(out/'absent-kit',out/'absent-output',over)
except ValueError as exc:assert 'requires a pinned equality report' in str(exc)
else:raise AssertionError('derive bypassed report gate')
try:dk.derive(out/'absent-kit',out/'valid-output',valid)
except FileNotFoundError:passed.append('derive accepts paired gate and reaches source authentication')
else:raise AssertionError('absent sealed kit accepted')
for field,value in [('status','DIFFERENT'),('regenerated',False),('selection_sha256','0'*64),('reference_sha256','0'*64),('tree_sha256','0'*64),('tool_sha256','0'*64),('raw_differences',['$.sources']),('fields',{}),('indices',{})]:
 bad=copy.deepcopy(report);bad[field]=value;refused(bind(bad,'bad_'+field),'equality report')
bad=copy.deepcopy(report);bad['inputs'].pop(next(iter(bad['inputs'])));refused(bind(bad,'bad_inventory'),'input inventory')
bad=copy.deepcopy(valid);bad['selection_equality']['sha256']='0'*64
bad['add_k']['selection_equality.json']=bad['selection_equality'];refused(bad,'pin differs')
bad=copy.deepcopy(valid);bad['add_k'].pop('selection_equality.json');refused(bad,'requires a pinned equality report')
changed=copy.deepcopy(candidate);changed['selected_rows']+=1
p=out/'changed.json';dk.write(p,changed)
bad=copy.deepcopy(valid);bad['add_k']['pool_selection_7test.json']=dict(path=str(p),sha256=dk.sha(p))
bad['config']['s1_routing']['selection']['sha256']=dk.sha(p);refused(bad,'selection content')
assert (H/'payload/d.py').read_bytes()==(H/'tools/derive_kit_h1.py').read_bytes()
# Run the complete deriver against the retained incomplete source fixture.
# Only the source-manifest authority is replaced in this test; all pin, archive,
# closure, authorization, report and config checks execute unchanged.
integration=copy.deepcopy(valid);integration.update(fixture=True,status='BLOCKED')
catalog=integration['config']['s1_routing']['catalog']
catalog.pop(dk.SELECTION_REFERENCE)
catalog[pin['sha256']]=integration['config']['s1_routing']['selection']['path']
launch=json.loads((H/'build/fx/k/launch.json').read_text())
cfg=json.loads((H/'build/fx'/launch['config']['file']).read_text())
cfg['s1_routing'].update(integration['config']['s1_routing'])
auth=json.loads((H/'payload/4.json').read_text());auth['config_sha256']=dk.identity(cfg)
ap=out/'TEST_ONLY_AUTH.json';dk.write(ap,auth)
integration['add_k']['4.json']=dict(path=str(ap),sha256=dk.sha(ap))
original_manifest=dk.SEALED_MANIFEST
fixture=H/'evidence/derivation/empty'
try:
 dk.SEALED_MANIFEST=dk.sha(fixture/'SHA256SUMS.txt')
 result=dk.derive(fixture,out/'derived',integration)
finally:dk.SEALED_MANIFEST=original_manifest
assert result['launch_status']=='FIXTURE' and result['config_identity']==dk.identity(cfg)
assert dk.sha(out/'derived/k/selection_equality.json')==valid['selection_equality']['sha256']
assert dk.sha(out/'derived/k/pool_selection_7test.json')==pin['sha256']
passed.append('full fixture derivation stores paired pins and remains FIXTURE')
(out/'results.json').write_text(json.dumps(dict(status='PASS',checks=passed,test_only=True),indent=2)+'\n')
(H/'evidence/fix7_selection/deriver_tests.json').write_text(json.dumps(dict(status='PASS',checks=len(passed),path=str(out),full_source_derivation='Complete fixture derivation passed with test-only source-manifest authority and proof. Exact sealed production kit is outside authorized workspace.'),indent=2)+'\n')
print(json.dumps(dict(status='PASS',checks=len(passed))))
