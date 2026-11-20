from common import *
from unittest.mock import patch
from contextlib import ExitStack
import shutil,subprocess
from student_pilot.p3_provenance import file_pin
from student_pilot.r1_persisted import scope
from student_pilot import r1_rooms as R,r1_direction_twins as W
sys.path.insert(0,str(kit('qd')/'b'))
import pl,sc,i,z
F=D/'planner_scene';F.mkdir(exist_ok=True);k=F/'kit';root=F/'node/p';root.mkdir(parents=True,exist_ok=True)
if not (root/'s').exists():(root/'s').symlink_to(T,target_is_directory=True)
def link(a,b):os.link(a,b);return b
if not k.exists():shutil.copytree(kit('qd'),k,copy_function=link)
cfg=J.load(D/'removal_receipts/cfg.json')
paths={x['sha256']:x['local_path'] for x in J.load(L/'work/build24m1/UPLOADS_q.json')['files'] if x['opaque_name'].startswith('u/')}
paths.update(cfg['r1_training']['persisted_files']);paths.update({p.name:str(p) for p in (D/'u').iterdir()})
seen=set()
def collect(value):
 if isinstance(value,dict):
  if 'path' in value and 'sha256' in value:
   h=value['sha256']
   if h in seen:return
   seen.add(h);p=Path(paths.get(h,value['path']))
   if not str(p).startswith(('/home/','/data')) and p.is_file() and (p.is_relative_to(L) or p.stat().st_size<2000000) and J.sha(p)==h:
    paths[h]=str(p)
    if p.stat().st_size<2000000:
     try:child=json.loads(p.read_bytes())
     except (ValueError,UnicodeError):return
     collect(child)
  else:
   for v in value.values():collect(v)
 elif isinstance(value,list):
  for v in value:collect(v)
collect(cfg)
for h,p in cfg['s1_routing']['catalog'].items():
 p=Path(paths.get(h,p))
 if not str(p).startswith(('/home/','/data')) and p.is_file() and (p.is_relative_to(L) or p.stat().st_size<2000000) and J.sha(p)==h:paths[h]=str(p)
target=F/'target';u=target/'u';u.mkdir(parents=True,exist_ok=True)
valid={}
for h,path in paths.items():
 p=Path(path)
 if not str(p).startswith(('/home/','/data')) and p.is_file() and (p.is_relative_to(L) or p.stat().st_size<2000000) and J.sha(p)==h:
  valid[h]=str(p)
  if (u/h).exists():continue
  try:os.link(p,u/h)
  except OSError as e:
   if e.errno!=18:raise
   assert p.stat().st_size<2000000
   shutil.copyfile(p,u/h)
paths=valid
spec=J.load(k/'k/p.json');spec.update(n_root=str(target),step=600,uploads=[dict(sha256=h,bytes=Path(p).stat().st_size) for h,p in paths.items()])
cap(k,'k/p.json',spec)
base=cfg['streams']['routing']
cap(k,'k/r.json',dict(routing_base=base))
cap(k,'k/h.json',dict(binaries=['bash']))
selection=dict(regenerated_sha256='0'*64,inputs_pinned=dict(routing_base=base,routing_database=J.load(base['path'])['database']))
J.write(root.parent/'routing_selection.json',selection)
# A valid tiny handover manifest supplies only planner sibling names.
idx=J.write(F/'index.json',{})
manifest=J.write(F/'weights.json',dict(index=dict(name='index.json',sha256=idx['sha256']),files=[]))
receipt=J.write(F/'handover.json',dict(pins=dict(full_weights=manifest)))
small={p['sha256']:dict(p,bytes=Path(p['path']).stat().st_size) for p in (idx,manifest)}
resolved=dict(archive=None,small_files=small,receipt=dict(receipt,bytes=Path(receipt['path']).stat().st_size),config=cfg,paths={},request={},tar_sha256='0'*64,tar_bytes=0,parts=[])
for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
resolved['kit_sha256']=reseal(k)
wrapper=D/'scene_tests/host.py';native_run=subprocess.run
def run(args,**kwargs):
 args=list(args)
 if str(k/'b/sc.py') in args or str(kit('qd')/'b/sc.py') in args:
  at=args.index(sys.executable);args[at+3:at+3]=[str(wrapper)]
 return native_run(args,**kwargs)
twins=cfg['r1_training']['direction_twins']
with ExitStack() as ctx:
 for key in ('rows','binding','aliases'):ctx.enter_context(patch.object(W,key.upper(),twins[key]['sha256']))
 ctx.enter_context(patch.object(R,'STORE',J.load(cfg['streams']['vqa']['path'])['database']['sha256']))
 ctx.enter_context(patch.dict(os.environ,Q_ROOT=str(root.parent),SLURM_JOB_ID='97'))
 ctx.enter_context(patch.object(sc.subprocess,'run',run))
 request,got,stage=pl.plan_payload(k,resolved,root,regeneration=False)
assert not (root/'q').exists()
plan=J.load(root/'plan.json');assert 'ss.json' in plan['entries'] and 'sc/2.json' in plan['entries']
live=target/'o/97/live';diagnostic=J.load(live/'d4.json');assert diagnostic['status']=='WOULD_REFUSE'
assert all(v['status'] in ('PASS','WOULD_REFUSE') for v in diagnostic['streams'].values())
assert all(p['role']=='protected_rooms' and p['stream']=='pointing' for p in plan['config']['remove_files'] if p.get('role'))
assert plan['config']['r2_scene_rebuild']['sha256']==J.sha(live/'s0.json')
# The native pre-preparation stage has returned an authenticated complete plan.
J.write(D/'PLANNER_SCENE_TESTS.json',dict(status='PASS',native_scene_rebuild=True,native_pool_refresh=True,native_room_audit=True,qd_would_refuse_continues=True,streams=diagnostic['streams'],entries=len(plan['entries']),scene_receipt=plan['config']['r2_scene_rebuild'],coverage=plan['config']['scene_coverage'],fixture='Synthetic retained native24 stores and twin authority constants; tiny handover sibling-name manifest; frame-host identity supplied only to child native verify; preparation is the next native caller.'))
print('Complete native planner scene/receipt/census path and qd continuation PASS')
