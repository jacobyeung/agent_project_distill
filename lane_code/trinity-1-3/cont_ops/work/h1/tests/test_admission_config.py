"""Audit the derived config with native CPU validators and hash-preserving local pins."""
import ast, copy, hashlib, json, os, subprocess, sys
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parents[1];root=H/'build/fx'
OUT=H/'evidence/fix6_admission';OUT.mkdir()
sys.path[:0]=[str(H/'build/tree'),str(root/'b'),str(H/'tools')]
os.environ['CUDA_VISIBLE_DEVICES']=''
from student_pilot import p3_provenance as provenance
# Relocate only already available bytes, retaining every SHA256 in the real config.
local={}
for directory in (H/'payload', root/'k'):
 for p in directory.iterdir():
  if p.is_file():local[hashlib.sha256(p.read_bytes()).hexdigest()]=p
original_pinned=provenance.pinned
class MissingLocalPin(ValueError):pass
def pinned(pin):
 if Path(pin['path']).is_relative_to(H):return original_pinned(pin)
 p=local.get(pin['sha256'])
 if p is None:raise MissingLocalPin('Unavailable local pinned input: '+pin['path']+' sha256='+pin['sha256'])
 return original_pinned(dict(path=str(p),sha256=pin['sha256']))
provenance.pinned=pinned
from student_pilot import carrier_c1_run as run, s1_admission, s1_route_policy, h1, carrier_c1_data as data
from student_pilot import checkpoint_space, trace_version
from student_pilot.carrier_c1_sweep import capped_steps
import derive_kit_h1 as dk
import d, i, v, x
la=json.loads((root/'k/launch.json').read_text());cfgpath=root/la['config']['file'];cfg=json.loads(cfgpath.read_text())
local[provenance.sha256(cfgpath)]=cfgpath
results={}
def passed(name,value=None):results[name]=dict(status='PASS',detail=value)
old=json.loads((H/'evidence/fix6_before/config.json').read_text())
try:run.validate(old)
except ValueError as e:
 assert str(e)=='Whole-leg checkpoint disk plan differs from the recipe',str(e)
 passed('round5_refusal',str(e))
else:raise AssertionError('round5 was admitted')
run.validate(cfg);passed('carrier_c1_run.validate')
h1.validate(cfg);passed('h1.validate',dict(stop=cfg['h1']['stop_after_step'],horizon=cfg['recipe']['steps']))
data.layout_settings(cfg);passed('data.layout_settings')
s1_route_policy.validate(cfg,authenticate=False);passed('s1_route_policy.shape')
try:s1_route_policy.validate(cfg)
except MissingLocalPin as e:results['s1_route_policy.authenticate']=dict(status='NOT RUN',detail=str(e))
else:passed('s1_route_policy.authenticate')
assert cfg['recipe']==run.recipe_for(cfg);passed('recipe_for')
assert cfg['checkpoint_disk_guard']==checkpoint_space.plan(cfg['recipe'],old['checkpoint_disk_guard']['reserve_bytes'])
budget=checkpoint_space.Budget(cfg['checkpoint_disk_guard'])
assert budget.remaining('export')==(16,3)
for _ in range(3):budget.remaining('export');budget.complete('export')
try:budget.remaining('export')
except ValueError as e:assert str(e)=='Whole-leg disk write budget is exhausted'
else:raise AssertionError('export budget overrun admitted')
passed('checkpoint_plan_budget',cfg['checkpoint_disk_guard'])
count=capped_steps(cfg['schedule'],cfg['recipe']['resume_every_seconds'],total_steps=cfg['recipe']['steps'],milestones=cfg['recipe']['milestones'])
passed('capped_steps',dict(result=count,applies_to_final_mode=False,reason='Only pose_only invokes this cap in run_steps; final mode uses recipe wall time.'))
trace_version.metadata(cfg);passed('trace_version.metadata')
value=d.contract(la,cfg);assert dk.digest(value)==json.loads((H/'ids.json').read_text())['contract'];passed('b.d.contract')
auth,actual=i.authorize(root,'p','0');assert actual==cfg;passed('b.i.authorize_p')
assert i.allocation_gpus('t',cfg)==4 and i.allocation_gpus('p',cfg)==0
x.ready(cfg,'p',auth);passed('b.x.ready_p_and_allocation_gpus')
v.tree(dict(path=str(root/'k/s1_record.json'),sha256=dk.sha(root/'k/s1_record.json')),H/'build/tree',la['source_revision']);passed('b.w.tree')
assert run.authenticate(cfg)==la['source_revision'];passed('run.authenticate', 'Native tree, import closure and archive verification; pins resolve to identical local bytes.')
assert cfg['h1']['stop_after_step']==200<400
passed('milestone_gate_branch',dict(enabled=run.step400_gate_enabled(cfg),reachable=False,reason='Fresh train starts at 0; H1 stops by 200. Native resume gate requires start_step >= 400.'))
results['milestone_gate']=dict(status='NOT RUN',detail='No m400 artifact/reports exist; branch unreachable for this 0..200 run.')
assert cfg['recipe']['wall_seconds']==86400 and la['slot']['wall_seconds']==46800
wrapper=(H/'runtime/jb.sh').read_text()
assert '-t 13:00:00' in wrapper and '--signal=B:USR1@3600' in wrapper and 'TK_JOB_START + 46800' in wrapper
passed('wall_and_allocation',dict(recipe=86400,allocation=46800,signal_at=43200,reason='b/g.py explicitly requires 86400; allocation safety uses USR1 bridge.'))
# Execute the wrapper's exact session-name validator with local dummy capabilities.
start=wrapper.index("/usr/bin/python3 -I -c '\nimport json, os, stat, sys")+len("/usr/bin/python3 -I -c '")
end=wrapper.index("' \"$KH/sess.json\"",start);script=wrapper[start:end]
names=(H/'EXPORT_OBJECTS.txt').read_text().splitlines();sessions=OUT/'sess.json';sessions.write_text(json.dumps(dict.fromkeys(names,'local-fixture-only')));sessions.chmod(0o600)
subprocess.run([sys.executable,'-I','-c',script,str(sessions),'17c4ffa4'],check=True)
assert all(f'q8/8865619b/17c4ffa4_{m}.tar.part{part:02d}-of-04' in names for m in ('m100','m200','mstop') for part in range(4))
passed('wrapper_session_names',dict(names=len(names),required_exports=['m100','m200','mstop'],real_capabilities_tested=False))
# Invoke real admit(): no fake preparation receipt or model. Stop on the first absent data pin.
out=OUT/'admit';out.mkdir()
try:s1_admission.admit(provenance.file_pin(cfgpath),out,value['frame_roots'],threads=1,prepare_only=True)
except MissingLocalPin as e:
 assert (out/'request.json').is_file(), 'admission stopped before authentication/request binding'
 results['admit']=dict(status='PARTIAL',detail=str(e),executed='CPU/resource/attempt bounds, world/filter/stream checks, validate, native authenticate, request binding, phase journal, parent full-LM warm-start check',not_executed='Parent metadata, stream materialization/exclusions, preparation, RGB audit, data receipt; missing production input bytes. prepare_only returns before CPU first batch.')
else:raise AssertionError('Expected production data to be unavailable locally')
results['gpu_pre_step']=dict(status='NOT RUN',detail='No GPU/model/production rows: allocation/CUDA/process-group/network, effective prepared receipt, model/processor/FSDP/optimizer setup, disk byte measurement, resume/binding and native first-step policy remain job-side. Pure config branches above passed.')
assert dk.identity(cfg)==json.loads((H/'ids.json').read_text())['identity']
(OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
