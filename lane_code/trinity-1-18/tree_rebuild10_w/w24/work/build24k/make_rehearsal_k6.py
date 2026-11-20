"""Prepare a fresh native-host rehearsal; run only through go_rehearsal_k.sh."""
from pathlib import Path
from copy import deepcopy
import sys,json,base64,hashlib,shutil,tarfile,os
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths_k6 import L,D,R
selected=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f')]
import joblib as J
from rehearsal_paths_k6 import reseal
from rehearsal_inputs_k6 import prepare
source=L/'work/build24f/rehearsal3'
if not source.exists():source=L/'work/build24f/rehearsal2'
if R.exists():raise ValueError('Fresh rehearsal directory required; preserve any existing attempt')
R.mkdir();(R/'tmp').mkdir();kit=R/'kit_n_go'
selected_seal=J.seal(selected)
shutil.copytree(selected,kit)
control=J.load(kit/'k/a.json');archive=kit/control['source']['path']
assert J.sha(archive)==control['source']['sha256']
with tarfile.open(archive) as stream:
 members=stream.getmembers()
 assert sum(m.size for m in members)<50_000_000
 assert all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
 stream.extractall(R/'source',members=members,filter='data')
from rehearsal_capacity_k6 import decide
decide(R,selected,J)
sys.path.insert(0,str(R/'source'))
from student_pilot.source_seal import create
from student_pilot.p3_provenance import source_files
cfg=J.load(source/'seed.json') if (source/'seed.json').exists() else J.load(source/'v.json')
for key in ('preparation','authorization','admission','readout'):cfg.pop(key,None)
for key in ('host_receipt','review'):cfg['r1_training'].pop(key,None)
cfg['r1_training']['stop_after_step']=6
point=Path('/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl')
h='d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'
assert J.sha(point)==h
cfg['remove_files'].insert(-1,dict(path=str(point),sha256=h))
cfg['r1_training']['launch22']['removal_order']=[p['sha256'] for p in cfg['remove_files']]

from student_pilot.checkpoint_space import plan
from student_pilot.carrier_c1_sweep import recipe_for
cfg['checkpoint_disk_guard']=plan(recipe_for(cfg),retained_archive_copies=1)
ns='/tmp/q_22c714e1';cfg['output']=ns+'/train'
def cap(path,value):
 doc=json.loads(path.read_text());raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
 doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());path.write_text(json.dumps(doc))
control=J.load(kit/'k/a.json');assert control['GO'] is True
tree=R/'source';closure={str(p.relative_to(tree)):J.sha(p) for p in source_files([tree/'student_pilot/carrier_c1_run.py'])}
code=create(tree,kit/control['source']['path'],closure,{},archive_path=ns+'/p2/q/t.tar')
cap(kit/'k/c0.json',code);raw=base64.b64decode(json.loads((kit/'k/c0.json').read_text())['payload'])
target=R/'target';(target/'u').mkdir(parents=True)
spec=J.load(kit/'k/p.json');spec.update(n_root=str(target),namespace=ns,code_sha256=hashlib.sha256(raw).hexdigest(),uploads=[],host_paths={},frame_roots=[])
# Native planning follows the fixture's exact pins and stream-reader closure.
# The production upload catalog contains unrelated stores and deferred slices.
spec['pin_paths']={}
cap(kit/'k/p.json',spec)
request=J.load(L/'work/build24d/go/r2.json');request.update(weights=False,device='cpu',memory_gib=16,
    routing_base=cfg['streams']['routing'],room_audit=cfg['r1_training']['room_audit'])
from rehearsal_population_k6 import bound_population
bound_population(R,L/'work/build24/proofs/capacity',cfg,J)
request['routing_base']=cfg['streams']['routing']
assert (R/'BOUNDED_POPULATION.json').is_file()
layout=prepare(R,L/'work/build24/proofs/capacity',cfg,J.write,J.sha)
request.pop('_paths',None)
request.pop('config',None)
request.update(frame_roots=layout['frame_roots'],staged_pins=[])
base=J.load(kit/'k/r.json');base['routing_base']=cfg['streams']['routing'];cap(kit/'k/r.json',base)
receipt=cfg['r1_training']['handover_receipt'];hand=J.load(receipt['path'])
small={}
for h,path in cfg['r1_training']['persisted_files'].items():
 p=Path(path);assert J.sha(p)==h;small[h]=dict(path=str(p),sha256=h,bytes=p.stat().st_size)
for pin in cfg['r1_training']['p_run'].values():
 p=Path(pin['path']);small[pin['sha256']]=dict(path=str(p),sha256=pin['sha256'],bytes=p.stat().st_size)
payload=D/'rehearsal_k/payload.tar'
assert payload.is_file()
part=dict(path=str(payload),sha256=J.sha(payload),bytes=payload.stat().st_size)
resolved=dict(kit_sha256=reseal(kit),config=cfg,request=request,archive=None,
    receipt=dict(receipt,bytes=Path(receipt['path']).stat().st_size),small_files=small,parts=[part],
    tar_sha256=part['sha256'],tar_bytes=part['bytes'],paths={h:ns+'/u/'+h for h in small},external_metadata=[])
from rehearsal_closure_k6 import inventory
inventory(selected,cfg,resolved,R,J)
J.write(R/'r2.json',dict(_resolved=resolved));J.write(R/'seed.json',cfg)
J.write(R/'FIXTURE_INPUTS.json',dict(source=str(source),seed_sha256=J.sha(source/'seed.json') if (source/'seed.json').exists() else J.sha(source/'v.json'),
    output=str(R),kit_source=str(selected),selected_seal=selected_seal,host_receipt='native q/RESULT.json.host_receipt',review='fixture only',
    differences=['tiny authenticated model and stores','CPU/gloo, four ranks','stop_after_step=6','effective milestones/checkpoints/budgets in rehearsal_boundary.py','synthetic review and zero-GPU CPU authorization']))

(R/'p').symlink_to('p2',target_is_directory=True)
assert J.seal(selected)==selected_seal
J.write(R/'SETUP.json',dict(kit_dir=str(selected),kit=selected_seal,fixture_kit=str(kit),source=control['source'],payload_reused=str(payload)))
