import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import ast,copy,subprocess,importlib.util
sys.path.insert(0,str(kit('n')/'b'))
import rb,ep
from student_pilot import s1_pool
from student_pilot.p3_provenance import file_pin,digest
from student_pilot.r1_persisted import scope
s=J.load(input_file('5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'))
r=J.load(input_file('0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a'))
rb.selection_check(s,r);rb.statuses(s['sources'],r['pool_selection_counts'])
mutations=[]
for name in sorted(s['sources']):
 for field in ('status','reason','retained','per_type'):
  v=copy.deepcopy(s);v['sources'][name][field]='MUTATED'
  try:rb.selection_check(v,r)
  except ValueError as e:assert str(e)=='R1_RECONSTRUCTION_SELECTION_DIFFERS:'+name;mutations.append(str(e)+':'+field)
  else:raise AssertionError('Accepted reconstruction mutation')
 v=copy.deepcopy(s['sources']);v[name]['status']='MUTATED'
 try:rb.statuses(v,s['sources'])
 except ValueError as e:assert str(e)=='R1_ROUTING_SOURCE_STATUS_DIFFERS:'+name;mutations.append(str(e))
 else:raise AssertionError('Accepted status mutation')
for code in ('selection','status'):
 v=copy.deepcopy(s);v['sources'].pop('U_Faithful')
 try:rb.selection_check(v,r) if code=='selection' else rb.statuses(v['sources'],s['sources'])
 except ValueError as e:mutations.append(str(e))
 else:raise AssertionError('Accepted missing source')
inputs=J.load(D/'CONFIG_INPUTS.json');seed=J.load(input_file(inputs['selection']['sha256']));m=J.load(input_file(inputs['manifest']['sha256']))
paths={};missing=[]
def remember(h):
 try:p=input_file(h)
 except ValueError:missing.append(h);return
 dst=D/'inputs'/h
 if not dst.exists():dst.write_bytes(p.read_bytes())
 paths[h]=str(dst)
remember(inputs['manifest']['sha256'])
for v in m['exclusions'].values():
 if not isinstance(v,dict):continue
 for key in ('list','withhold','v2'):
  if key in v:remember(v[key+'_sha256'])
try:
 with scope(paths):pool=s1_pool.Pool(seed['manifest'],seed['room_sets'])
 constructor=dict(status='PASS')
except ValueError as error:
 constructor=dict(status='UNAVAILABLE',refusal=str(error))
 pool=s1_pool.Pool.__new__(s1_pool.Pool)
 pool.sources={v['name']:v for v in m['sets']};pool.room_sets=seed['room_sets']
policy={n:dict(status='DEFERRED' if pool.deferred(n) else 'ELIGIBLE',reason=pool.deferred(n)) for n in pool.sources}
rb.statuses(policy,s['sources'])
assert len(policy)==14
for n in NAMES:
 for f in ('k/c.json','k/n.json'):
  before=J.load(L/'attic/build24m4h'/kit(n).relative_to(L)/f);after=J.load(kit(n)/f)
  assert before['remove_files']==after['remove_files']
  assert before['r1_training']['p_run']==after['r1_training']['p_run']
  assert after['s1_routing']['selection']==inputs['selection']
# Run the real prepare entrypoint with local metadata. Never replace row bodies.
cfg=J.load(kit('n')/'k/c.json')
for v in cfg['remove_files']:remember(v['sha256'])
if seed.get('tokenizer'):remember(seed['tokenizer']['sha256'])
for v in seed['sources'].values():
 if v.get('source'):remember(v['source']['sha256'])
try:
 with scope(paths):
  prepared=s1_pool.prepare(seed['manifest'],D/'prepare_probe',cfg['remove_files'],seed['tokenizer'],seed['room_sets'])
 prepare_result=dict(returned=True,statuses={n:v['status'] for n,v in prepared['sources'].items()},reasons={n:v.get('reason') for n,v in prepared['sources'].items()})
except Exception as e:prepare_result=dict(returned=False,error=type(e).__name__+': '+str(e))
# Publish actual bytes after a simulated producer writes diagnostics then raises.
publication=[]
for mode,prefix in (('q','p'),('r','dr/p')):
 node=D/('publication_'+mode);target=D/('published_'+mode);target.mkdir()
 try:
  J.write(node/prefix/'q/selection/materialization.json',dict(status='BLOCKED',blockers=['synthetic-test']))
  J.write(node/prefix/'q/selection/receipt.json',dict(count=0))
  J.write(node/prefix/'i/pool/r.json',dict(status='REFUSE',refusal='synthetic-test'))
  raise ValueError('synthetic-test')
 except ValueError:
  records=ep.publish_artifacts(target,node)
 assert len(records)==6
 for name,v in records.items():assert (target/name).read_bytes()==(node/v['source']).read_bytes()
 # A lone artifact must survive too; publication never requires its pair.
 J.write(node/prefix/'q/base/materialization.json',dict(status='BLOCKED'))
 records=ep.publish_artifacts(target,node);assert len(records)==7
 publication.append(dict(mode=mode,files=records))
# P's exact sealed files run in a separate isolated interpreter.
probe=D/'p_probe.py';probe.write_text('''import sys,json,ast
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from student_pilot import s1_pool
from student_pilot.p3_provenance import load,file_pin
s=load(sys.argv[2]);assert s['implementation']==s1_pool.implementation()
p=Path(sys.argv[1])/'student_pilot/s1_routing.py';t=ast.parse(p.read_text())
n=next(n for n in ast.walk(t) if isinstance(n,ast.If) and any(isinstance(x,ast.Constant) and x.value=='Routing selection belongs to another implementation' for x in ast.walk(n)))
exec(compile(ast.Module(body=[n],type_ignores=[]),str(p),'exec'),dict(selection=s,s1_pool=s1_pool))
try:next(s1_pool.selected_rows(file_pin(sys.argv[2]),'ARKIT_gaps'))
except ValueError as e:
 assert 'implementation differs' not in str(e);print('NATIVE_READER_POST_GUARD',str(e))
else:raise AssertionError('Production row body unexpectedly available')
print('P_IMPLEMENTATION_GUARDS_PASS',len(s['implementation']))
''')
p=subprocess.run([sys.executable,'-I','-s','-B',str(probe),str(D/'p_tree'),str(input_file('5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'))],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(D/'p_probe.log').write_text(p.stdout);assert p.returncode==0,p.stdout
J.write(D/'OFFLINE.json',dict(status='PASS',guard_mutations=mutations,policy_statuses=policy,native_constructor=constructor,native_prepare=prepare_result,missing_inputs=sorted(set(missing)),publication=publication,P_guard_output=p.stdout,P_archive_local_hash=J.sha(D/'p.tar'),P_tree_inventory_exact=True,P_archive_not_original=True,not_exercised=['Production row preparation','Production materialization','Full 4e8e6c04 database hash','Orchard mount layout and processor assets']))
print('OFFLINE PASS',len(mutations),'mutation refusals; 14 native manifest policies; prepare',prepare_result)
