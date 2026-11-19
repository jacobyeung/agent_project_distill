"""Prepare a fresh native-host rehearsal; run only through go_rehearsal_k.sh."""
from pathlib import Path
from copy import deepcopy
import sys,json,base64,hashlib,shutil,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';R=D/'rehearsal_k'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f'),str(L/'work/tree_r1')]
import joblib as J
from kit24f import reseal
from student_pilot.source_seal import create
from student_pilot.p3_provenance import source_files
source=L/'work/build24f/rehearsal3'
if not source.exists():source=L/'work/build24f/rehearsal2'
if R.exists():raise ValueError('Fresh rehearsal directory required; preserve any existing attempt')
R.mkdir();(R/'tmp').mkdir();kit=R/'kit_n_go';shutil.copytree(L/'out/kit_n_go',kit)
cfg=J.load(source/'seed.json') if (source/'seed.json').exists() else J.load(source/'v.json')
for key in ('preparation','authorization','admission','readout'):cfg.pop(key,None)
for key in ('host_receipt','review'):cfg['r1_training'].pop(key,None)
cfg['r1_training']['stop_after_step']=6
from student_pilot.checkpoint_space import plan
from student_pilot.carrier_c1_sweep import recipe_for
cfg['checkpoint_disk_guard']=plan(recipe_for(cfg),retained_archive_copies=1)
ns='/tmp/q_22c714e1';cfg['output']=ns+'/p2/q/r'
def cap(path,value):
 doc=json.loads(path.read_text());raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
 doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());path.write_text(json.dumps(doc))
control=J.load(kit/'k/a.json');assert control['GO'] is True
tree=L/'work/tree_r1';closure={str(p.relative_to(tree)):J.sha(p) for p in source_files([tree/'student_pilot/carrier_c1_run.py'])}
code=create(tree,kit/control['source']['path'],closure,{},archive_path=ns+'/p2/q/t.tar')
cap(kit/'k/c0.json',code);raw=base64.b64decode(json.loads((kit/'k/c0.json').read_text())['payload'])
target=R/'target';(target/'u').mkdir(parents=True)
spec=J.load(kit/'k/p.json');spec.update(n_root=str(target),namespace=ns,code_sha256=hashlib.sha256(raw).hexdigest(),uploads=[],host_paths={},frame_roots=[])
inputs=J.load(L/'work/build24i/UPLOADS_n.json')['files']
for item in inputs:
 if item['opaque_name'].startswith('u/'):
  shutil.copyfile(item['local_path'],target/'u'/item['sha256'])
  spec['uploads'].append(dict(sha256=item['sha256'],bytes=item['bytes']))
cap(kit/'k/p.json',spec)
request=J.load(L/'work/build24d/go/r2.json');request.update(weights=False,device='cpu',memory_gib=16,
    routing_base=cfg['streams']['routing'],room_audit=cfg['r1_training']['room_audit'])
base=J.load(kit/'k/r.json');base['routing_base']=cfg['streams']['routing'];cap(kit/'k/r.json',base)
receipt=cfg['r1_training']['handover_receipt'];hand=J.load(receipt['path'])
small={}
for h,path in cfg['r1_training']['persisted_files'].items():
 p=Path(path);assert J.sha(p)==h;small[h]=dict(path=str(p),sha256=h,bytes=p.stat().st_size)
for pin in cfg['r1_training']['p_run'].values():
 p=Path(pin['path']);small[pin['sha256']]=dict(path=str(p),sha256=pin['sha256'],bytes=p.stat().st_size)
export=Path(cfg['init_artifact']['artifact']['path']).parent
payload=R/'payload.tar'
with tarfile.open(payload,'w') as out:
 for p in sorted(export.rglob('*')):
  if p.is_file():out.add(p,arcname=str(p.relative_to(export)),recursive=False)
part=dict(path=str(payload),sha256=J.sha(payload),bytes=payload.stat().st_size)
resolved=dict(kit_sha256=reseal(kit),config=cfg,request=request,archive=None,
    receipt=dict(receipt,bytes=Path(receipt['path']).stat().st_size),small_files=small,parts=[part],
    tar_sha256=part['sha256'],tar_bytes=part['bytes'],paths={h:ns+'/u/'+h for h in small},external_metadata=[])
J.write(R/'r2.json',dict(_resolved=resolved));J.write(R/'seed.json',cfg)
J.write(R/'FIXTURE_INPUTS.json',dict(source=str(source),seed_sha256=J.sha(source/'seed.json') if (source/'seed.json').exists() else J.sha(source/'v.json'),
    output=str(R),kit_source=str(L/'out/kit_n_go'),host_receipt='native q/RESULT.json.host_receipt',review='fixture only',
    differences=['tiny authenticated model and stores','CPU/gloo, four ranks','stop_after_step=6','effective milestones/checkpoints/budgets in rehearsal_boundary.py','synthetic review and zero-GPU CPU authorization']))
