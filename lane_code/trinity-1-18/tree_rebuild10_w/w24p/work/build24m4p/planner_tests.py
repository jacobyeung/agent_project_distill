import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import copy, importlib.util
from contextlib import ExitStack
from unittest.mock import patch
from student_pilot.p3_provenance import file_pin
from student_pilot import p3_provenance as provenance
from student_pilot import r1_rooms
import pl, px, i, rb, sc, cs, rv

F=D/('planner_'+str(time.time_ns()));F.mkdir();records=[]
DB='4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'
BASE='ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984'

for mode in ('r','q'):
 root=F/mode;root.mkdir();(root/'native').mkdir();(root/'live').mkdir();store=root/'store';store.mkdir();paths={};calls=[]
 def pin(name,value,h=None):
  p=store/name;write(p,value);h=h or z.sha(p);paths[h]=str(p);return dict(path='u/'+h,sha256=h)
 tiny=pin('tiny',{})
 model=pin('asset',dict(files={}))
 recipe=pin('recipe',dict(inputs=dict(catalog={}),legacy=tiny,division=tiny,base_model=model))
 base=pin('base',dict(database=dict(path='u/'+DB,sha256=DB),materialization=recipe),BASE)
 p_cfg=pin('p',dict(streams=dict(routing=base),code=tiny,remove_files=[],dev_scene_exclusions=tiny,benchmark_scene_exclusions=tiny))
 pool=pin('pool',dict(manifest=tiny,tokenizer=None))
 idx=pin('index',{})
 weights=pin('weights',dict(index=dict(name='index.json',sha256=idx['sha256']),files=[]))
 receipt=pin('receipt',dict(pins=dict(full_weights=weights)))
 if mode=='q':
  p=store/'db';p.write_bytes(b'SQLite fixture');paths[DB]=str(p)
 cfg=dict(streams=dict(routing=base),s1_routing=dict(selection=pool,catalog={}),
          r1_training=dict(p_run=dict(config=p_cfg),persisted_files={}),r2_all_stream_exclusions=True)
 resolved=dict(kit_sha256=z.seal(kit('qd')),archive=None,receipt=dict(path=paths[receipt['sha256']],sha256=receipt['sha256'],bytes=Path(paths[receipt['sha256']]).stat().st_size),
    config=cfg,request=dict(routing_base=base),paths={},tar_sha256='0'*64,tar_bytes=0,parts=[],small_files={h:dict(path=p,bytes=Path(p).stat().st_size) for h,p in paths.items()})
 spec=z.load(kit('qd')/'k/p.json');spec=dict(spec,uploads=[],n_root=str(store))
 old_load=pl.load;old_checked=pl.checked;old_sha=pl.sha
 def checked(p,h,size=None):
  if h in (BASE,DB):
   assert Path(p).is_file();return Path(p)
  return old_checked(p,h,size)
 def need(k,r,sources):
  def get(h,field):
   sources[h]=paths[h];return paths[h]
  return get
 def reconstruct(c,scratch):
  calls.append('P');assert not (root/'native/q').exists()
  (scratch/'base').mkdir();p=scratch/'base/rows.sqlite';p.write_bytes(b'SQLite fixture');paths[DB]=str(p)
  for name in ('base_input.json','base_mounts.json','base_imports.json'):write(scratch/name,{})
  (scratch/'base_tree').mkdir();(scratch/'base_tree/a.py').write_text('pass\n')
  return p
 def bind(c,sources,scratch,dest,k,**kw):
  calls.append('scene');assert DB in sources and Path(sources[DB]).is_file()
  assert kw['pool_inputs']['manifest']==tiny
  physical=scratch/'sc/sc';physical.mkdir(parents=True)
  write(physical/'pool.json',dict(sources={}))
  poolpin=dict(path=str(dest/'sc/pool.json'),sha256=z.sha(physical/'pool.json'))
  write(physical/'2.json',dict(pool_selection=poolpin));write(physical/'0.json',{})
  c.update(r2_scene_rebuild=dict(path=str(dest/'sc/2.json'),sha256=z.sha(physical/'2.json')),scene_coverage={})
  c['s1_routing']['selection']=poolpin
  return physical
 native_pin=provenance.pinned
 with ExitStack() as stack:
  stack.enter_context(patch.object(provenance,'pinned',side_effect=lambda pin:Path(paths[pin['sha256']]) if pin['sha256'] in (BASE,DB) else native_pin(pin)))
  stack.enter_context(patch.object(pl,'load',side_effect=lambda p:spec if Path(p)==kit('qd')/'k/p.json' else old_load(p)))
  stack.enter_context(patch.object(pl,'checked',side_effect=checked))
  stack.enter_context(patch.object(pl,'sha',side_effect=lambda p:DB if Path(p).name=='rows.sqlite' else old_sha(p)))
  stack.enter_context(patch.object(pl,'selection_pin',return_value=None))
  stack.enter_context(patch.object(px,'resolver',side_effect=need))
  stack.enter_context(patch.object(i,'refresh',side_effect=lambda req,scratch:req))
  stack.enter_context(patch.object(rb,'reconstruct',side_effect=reconstruct))
  stack.enter_context(patch.object(r1_rooms,'census',return_value=({},None)))
  stack.enter_context(patch.object(r1_rooms,'verify_audit'))
  stack.enter_context(patch.object(sc,'bind',side_effect=bind))
  stack.enter_context(patch.object(cs,'sources',return_value={}))
  stack.enter_context(patch.object(rv,'location',return_value=(root/'live',None)))
  stack.enter_context(patch.dict(os.environ,SLURM_JOB_ID='123'))
  request,sources,stage=pl.plan_payload(kit('qd'),resolved,root/'native',regeneration=mode=='r')
  plan=z.load(root/'native/plan.json')
  assert plan['config']['s1_routing']['selection']['path'].endswith('/sc/pool.json')
  assert calls==(['P','scene'] if mode=='r' else ['scene']),calls
  assert 'sc/pool.json' in plan['entries']
  if mode=='r':
   assert 'base/rows.sqlite' in plan['entries'] and 'base_tree/a.py' in plan['entries']
   assert 'base_input.json' in plan['entries'] and 'base_mounts.json' in plan['entries']
  records.append(dict(mode=mode,calls=calls,staged_pool=True,early_P=mode=='r'))
  stage.close()

# Exercise sc.bind's actual configuration assignments with only the subprocess boundary replaced.
root=F/'bind';root.mkdir();scratch=root/'i';scratch.mkdir();dest=root/'q';sources={}
def pin(name,value):
 p=root/name;write(p,value);pin=file_pin(p);sources[pin['sha256']]=str(p);return pin
db=pin('rows',{})
one=pin('one',dict(database=db,count=1))
pose=pin('pose',dict(sources=[dict(receipt=one),dict(receipt=one)]))
pool=pin('pool',dict(manifest=db,tokenizer=None))
cfg=dict(streams=dict(pose=pose,vqa=one,routing=one,pointing=one),s1_routing=dict(selection=pool),remove_files=[])
def child(cmd,**kw):
 physical=scratch/'sc/sc';physical.mkdir()
 write(physical/'2.json',dict(pool_selection=dict(path=str(dest/'sc/p.json'),sha256='a'*64),scene_coverage=dict(fixture=True)))
 return type('Result',(),dict(returncode=0))()
before=copy.deepcopy(cfg)
with patch.object(sc.subprocess,'run',side_effect=child),patch('shutil.which',return_value='/usr/bin/bwrap'):
 sc.bind(cfg,sources,scratch,dest,kit('qd'))
assert cfg['s1_routing']['selection']['sha256']=='a'*64
assert cfg['streams']==before['streams']
write(D/'PLANNER_TESTS.json',dict(status='PASS',records=records,sc_bind_selection=True,scope='Actual planners; authenticated local metadata; P producer and scene child stubbed, native census tested separately.'))
print('Planner r/q ordering, staged P artifacts and sc pool binding PASS')
