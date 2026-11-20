from pathlib import Path
import sys,os,json,shutil,subprocess,importlib.util,copy,time
from types import SimpleNamespace
from contextlib import ExitStack
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4x2'
sys.path[:0]=[str(D),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
from common import *
from student_pilot import p3_provenance as provenance,r1_rooms
import pl,px,i,rb,sc,cs,rv
sp=importlib.util.spec_from_file_location('xx',L/'out/rcj/x.py');X=importlib.util.module_from_spec(sp);sp.loader.exec_module(X)
R=D/'real/node';records=[]
if sys.argv[1] in ('child','run_child'):
 import atexit
 events=[]
 def audit(event,args):
  write=False;path=None
  if event=='open' and isinstance(args[0],(str,bytes)):
   write=bool(args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC));path=os.fsdecode(args[0])
  elif event in ('os.mkdir','os.chmod','os.rename','os.link','os.symlink'):
   write=True;path=os.fsdecode(args[0])
  elif event in ('os.remove','os.rmdir'):raise RuntimeError('NO_DELETION')
  if write:
   p=Path(path).absolute()
   events.append(dict(event=event,path=str(p)))
   assert p.is_relative_to(R) or p.is_relative_to('/tmp/q_22c714e1'),(event,path)
 def finish():
  (R/('writes_'+sys.argv[1]+'.json')).write_text(json.dumps(events,indent=2)+'\n')
 sys.addaudithook(audit);atexit.register(finish)
 DB='4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'
 BASE='ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984'
 
 for mode in ('r',):
  root=Path('/tmp/q_22c714e1');store=root/('store_r' if sys.argv[1]=='run_child' else 'store');store.mkdir(exist_ok=True);paths={};calls=[]
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
   calls.append('P');assert not (root/'z/q').exists()
   (scratch/'base').mkdir(exist_ok=True);p=scratch/'base/rows.sqlite';p.write_bytes(b'SQLite fixture');paths[DB]=str(p)
   for name in ('base_input.json','base_mounts.json','base_imports.json'):write(scratch/name,{})
   (scratch/'base_tree').mkdir(exist_ok=True);(scratch/'base_tree/a.py').write_text('pass\n')
   return p
  def bind(c,sources,scratch,dest,k,**kw):
   calls.append('scene');assert DB in sources and Path(sources[DB]).is_file()
   assert kw['pool_inputs']['manifest']==tiny
   physical=scratch/'sc/sc';physical .mkdir(parents=True,exist_ok=True)
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
   stack.enter_context(patch.dict(os.environ,SLURM_JOB_ID='173724'))
   z.write(R/'resolved.json',resolved)
   if sys.argv[1]=='run_child': z.write(R/'dr/r.json',dict(_resolved=resolved))
   inputs=SimpleNamespace(spec=spec,records={},sources={},archives={})
   inputs.need=lambda h,field: paths[h]
   stack.enter_context(patch.object(X,'Inputs',return_value=inputs))
   if sys.argv[1]=='child':
    X.plan_r(kit('qd'),R,'173724')
   else:
    import launch_r1.entry as entry,rg,sqlite3
    from student_pilot import carrier_c1_run,r1_coverage
    from launch_r2 import staging as staging_module
    def begin(cfg,directory,request):
     directory.mkdir(exist_ok=True);return directory,directory,{}
    def staging(cfg,directory,request,job_tmp,stage=None):
     stage(z.load(provenance.pinned(request['staging']))['entries'],directory)
     return cfg
    def payload(k,final,directory):
     (directory/'u').mkdir(exist_ok=True)
    def regenerate(cfg,directory,compare=True):
     (directory/'selection').mkdir(exist_ok=True)
     with sqlite3.connect(directory/'selection/rows.sqlite') as db:
      db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
     z.write(directory.parent/'routing_selection.json',{})
     return {}
    stack.enter_context(patch.object(carrier_c1_run,'identity',return_value='fixture'))
    stack.enter_context(patch.object(entry,'check_host_runtime'))
    stack.enter_context(patch.object(entry,'check_host_scene'))
    stack.enter_context(patch.object(staging_module,'validate_plan'))
    stack.enter_context(patch.object(r1_coverage,'routing_request',return_value=True))
    stack.enter_context(patch.object(z,'copy_resolved_payload',side_effect=payload))
    stack.enter_context(patch.object(rg,'regenerate',side_effect=regenerate))
    X.run_r(kit('qd'),R,'173724')
    assert (root/'p/q/selection/rows.sqlite').is_file()
    assert (root/'p/q/staging.json').exists() is False
    print('RUN_PASS',flush=True)
    raise SystemExit(0)
   plan=z.load(root/'z/plan.json')
   assert plan['config']['s1_routing']['selection']['path'].endswith('/sc/pool.json')
   assert calls==(['P','scene'] if mode=='r' else ['scene']),calls
   assert 'sc/pool.json' in plan['entries']
   if mode=='r':
    assert 'base/rows.sqlite' in plan['entries'] and 'base_tree/a.py' in plan['entries']
    assert 'base_input.json' in plan['entries'] and 'base_mounts.json' in plan['entries']
   records.append(dict(mode=mode,calls=calls,staged_pool=True,early_P=mode=='r'))
   assert (R/'pins.json').is_file() and (R/'dr/r.json').is_file()
   print('PLAN_PASS',flush=True)
 
else:
 label=sys.argv[1]
 F=D/'real'
 if label!='RUN' and F.exists():F.rename(D/('real_saved_'+str(time.time_ns())))
 if label!='RUN': R .mkdir(parents=True,exist_ok=True)
 (R/'dr').mkdir(exist_ok=True);(R/'g').mkdir(exist_ok=True);(R/'g'/R.relative_to('/scratch')) .mkdir(parents=True,exist_ok=True)
 
 for path in (L,Path(sys.prefix),Path(sys.base_prefix)):
  if path.is_relative_to('/scratch'):(R/'g'/path.relative_to('/scratch')).mkdir(parents=True,exist_ok=True)
 (R/'v').mkdir(exist_ok=True);(R/'cl').mkdir(exist_ok=True);(R/'cl/site_alias').mkdir(exist_ok=True)
 pool=F/'pool';pool.mkdir(exist_ok=True);(pool/'o').mkdir(exist_ok=True)
 z.write(R/'mode.json',dict(mode='r'))
 z.write(R/'env.json',dict(venv=str(R/'v'),scratch=str(R/'g'),paths=[str(L/'out/kit_qd/b')],record=str(R/'e.json')))
 class Pins:
  load=staticmethod(z.load)
  checked=staticmethod(lambda p,h:Path('/project/community/jjyeung/cp4tk_rt/kit/bwrap'))
 real_run=subprocess.run
 def adapted(cmd,**kw):
  original=list(cmd);cmd=list(cmd);cmd[0]=shutil.which('bwrap')
  at=cmd.index('--bind');extra=[]
  for path in dict.fromkeys((str(L),sys.prefix,sys.base_prefix)):
   extra+=['--ro-bind',path,path]
  extra+=['--ro-bind',str(pool),'/project/community/jjyeung/okh7/x_22c714e1']
  cmd[at:at]=extra
  at=cmd.index('--chdir')+2
  cmd[at:]=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'run_child' if label=='RUN' else 'child']
  z.write(D/(label+'_COMMAND.json'),dict(original=original,command=cmd,adapters=extra))
  return real_run(cmd,**kw)
 with patch.object(X,'attach',return_value=Pins),patch.object(X.subprocess,'run',side_effect=adapted):
  rc=X.launch(kit('qd'),R,'173724',action='run' if label=='RUN' else 'plan')
 if rc:raise ValueError('R1_PLAN_REFUSED:'+str(rc))
 print('REAL_PATH_PASS',flush=True)
