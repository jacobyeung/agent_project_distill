"""Local two-rank rehearsal of the native stop trap, rank loop and end slot."""
import datetime,hashlib,importlib.util,json,os,signal,socket,sqlite3,subprocess,sys,time,traceback
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';P=L/'work/build8/proofs/stop_multirank'
sys.path[:0]=[str(T),str(T/'generator/derivgen_v7')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(P),STUDENT_FRAME_ROOT_MAP='{}',STUDENT_ORCHARD='1')
PY=[sys.executable,'-I','-s','-B']
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tmp_size():
 value=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file() and not p.is_symlink())
 if value>200_000_000:raise RuntimeError('temporary storage policy')
 return value
def marked(path,key):
 try:return bool(json.loads(path.read_text()).get(key))
 except (OSError,json.JSONDecodeError):return False
def module(name):
 sys.path.insert(0,str(T/'launch_s1/b'))
 spec=importlib.util.spec_from_file_location('native_'+name,T/'launch_s1/b'/f'{name}.py')
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def rank(root,case):
 import torch,torch.distributed as dist
 from student_pilot import carrier_c1_run as R
 from student_pilot.carrier_c1 import parameter_groups
 from student_pilot.p3_provenance import file_pin
 from tests.test_carrier_c1 import fixture
 from tests.test_r2_data_path import TinyProcessor
 torch.set_num_threads(4);r=int(os.environ['RANK']);stop=[False]
 def requested(*args):
  stop[0]=True;write(root/f'signal_{r}.json',{'rank':r,'received':True})
 signal.signal(signal.SIGUSR1,requested)
 dist.init_process_group('gloo',rank=r,world_size=2,timeout=datetime.timedelta(seconds=45))
 try:
  model,_,_=fixture(training_mode='pose_only',depth_enabled=False)
  model.base.resize_token_embeddings(512) if hasattr(model,'base') else None
  # CarrierC1 keeps the native language model and LM head as separate modules.
  if model.get_input_embeddings().num_embeddings<512:
   from transformers import Qwen3_5ForConditionalGeneration
   from student_pilot.carrier_c1 import CarrierC1
   cfg=model.config;cfg.text_config.vocab_size=512
   base=Qwen3_5ForConditionalGeneration(cfg).float()
   model=CarrierC1(base,dict(embed_dim=64,num_heads=4,trunk_depth=4,refine_iterations=4,
      weight_gravity=.05,weight_scale=.02,supervision={'path':'/fixture','sha256':'a'*64}),{},5,
      training_mode='pose_only',depth_enabled=False)
  device=torch.device('cpu');wrapped=R.wrap_model(model,device,mixed_precision=False)
  optimizer=torch.optim.AdamW(parameter_groups(wrapped))
  receipt=json.loads((P/'data/receipt.json').read_text());rows=R.Rows(receipt,TinyProcessor())
  cfg=dict(training_mode='pose_only',base_identity='tiny-local-boundary',trace_program_version='3.13',
    steps=4,milestones=[2,4],schedule=dict(startup_seconds=1,p95_step_seconds=1,checkpoint_seconds=1,export_seconds=1),
    checkpoint_disk_guard=dict(reserve_bytes=85*1024**3),
    recipe=dict(export_at_stop=True),stop_after_step=1 if case=='fallback' else None)
  # Pose-only recipe keeps its native logical batch. This proof checks stop
  # synchronization on two transport ranks, not production batch equivalence.
  from student_pilot.carrier_c1_sweep import recipe_for
  cfg['recipe']=recipe_for(cfg);cfg['recipe']['export_at_stop']=True
  def profile(frame,event,arg):
   if event=='call' and frame.f_code is R.optimize_step.__code__ and frame.f_locals.get('step')==2 and case=='signal':
    write(root/f'ready_{r}.json',{'next_step':2})
    end=time.monotonic()+90
    while not marked(root/'release.json','signal_received'):
     if time.monotonic()>end:raise TimeoutError('signal coordinator did not release ranks')
     time.sleep(.05)
  sys.setprofile(profile)
  try:report=R.run_steps(model,wrapped,optimizer,rows,{'pose':1},root,cfg,{'fixture':'native-stop'},device,rank=r,stop=stop)
  finally:sys.setprofile(None);rows.close()
  expected=2 if case=='signal' else 1
  assert report['last_step']==expected,report
  write(root/f'rank_{r}.json',dict(last_step=report['last_step'],stopped=report['stopped_for_resume']))
  dist.barrier()
  if r==0:
   fresh=type(model)
   from transformers import Qwen3_5ForConditionalGeneration
   base=Qwen3_5ForConditionalGeneration(model.config).float()
   loaded=fresh(base,dict(embed_dim=64,num_heads=4,trunk_depth=4,refine_iterations=4,
      weight_gravity=.05,weight_scale=.02,supervision={'path':'/fixture','sha256':'a'*64}),{},5,
      training_mode='pose_only',depth_enabled=False)
   R.load_artifact(loaded,file_pin(root/f'm{expected}/artifact.json'))
   reader=R.Rows(receipt,TinyProcessor());batch,target,audit=reader.get('pose',0)
   with torch.no_grad():finite=bool(torch.isfinite(loaded(batch,target)['loss']))
   reader.close();assert finite
   write(root/'reload.json',dict(finite=finite,artifact=file_pin(root/f'm{expected}/artifact.json')))
  dist.barrier()
 finally:dist.destroy_process_group()
def supervise(root,case):
 native=module('i');children=[]
 signal.signal(signal.SIGUSR1,lambda *_:native.relay(os.getpid()))
 for r in range(2):
  env={**os.environ,'LOCAL_RANK':str(r),'RANK':str(r),'WORLD_SIZE':'2',
       'OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','NUMEXPR_NUM_THREADS':'4'}
  children.append(subprocess.Popen(PY+[str(Path(__file__).resolve()),'rank',str(root),case],env=env))
 codes=[p.wait() for p in children]
 raise SystemExit(0 if codes==[0,0] else 1)
def setup():
 from tests.test_r2_data_path import fixture
 from student_pilot.p3_provenance import file_pin
 from student_pilot.pose_samples import AUGMENT,SCHEMA
 import numpy as np
 data=P/'data';data.mkdir(exist_ok=True);row=fixture(data,stream='pose')
 row['student_input']['frames']=[file_pin(data/'frames'/f'{i}.png') for i in range(0,64,2)]
 row['student_input']['frame_prefix']=str(data/'frames')
 target=row['target_record'];target['point_depth']['mask']=[[False]]*32
 for i,c in enumerate(target['camera']):target['camera'][i]=[*c[:2],i*.01,*c[3:]]
 from student_pilot.camera_targets import trajectory_scale
 target['trajectory_scale']=trajectory_scale(target['camera'],target['camera_mask'])
 row.update(category='camera_pose_only',pose_sample=dict(schema=SCHEMA,recording=dict(sampling=dict(variant='all_frames32')),
  frames=32,positions=list(range(32)),temporal_grouping='fused_pairs_all_frames',anchors=list(range(1,33)),
  augment={**AUGMENT,'seed':17,**{k:0 for k in ('brightness','contrast','saturation','hue','blur_p','grayscale_p')}},metric=True,
  **{k:target[k] for k in ('camera','camera_mask','trajectory_scale','gravity','gravity_mask')}))
 database=data/'rows.sqlite'
 with sqlite3.connect(database) as c:
  c.execute('CREATE TABLE IF NOT EXISTS rows (i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
  c.execute('INSERT OR REPLACE INTO rows VALUES (0,?,?)',(json.dumps(row),json.dumps(target)))
 write(data/'receipt.json',dict(training_mode='pose_only',streams={'pose':dict(count=1,database=file_pin(database))}))
 source=(T/'launch_s1/b/r.sh').read_text()
 trap=source[source.index('on_stop() {'):source.index('trap on_stop USR1')+len('trap on_stop USR1')]
 trap=trap.replace('/usr/bin/python3 -I',sys.executable+' -I -s -B')
 # The launch admission and GPU allocation setup are outside this CPU proof.
 # The signal handler, forwarder, relay and rank loop are native source.
 (P/'b').mkdir(exist_ok=True);(P/'b/h.py').write_bytes((T/'launch_s1/b/h.py').read_bytes())
 (P/'b/i.py').write_text('import runpy,sys\nsys.argv=["'+str(Path(__file__).resolve())+'","supervise",*sys.argv[1:]]\nrunpy.run_path(sys.argv[0],run_name="__main__")\n')
 shell='#!/bin/bash\nset -euo pipefail\nHX="$1"\nX="$1"\nNX="$1"\nstop_file="$2/request.stop"\nchild=""\nadmission_child=""\n'+trap+'\nexport K3="$stop_file" R1_STOP_FILE="$stop_file"\n"$4" -I -s -B "$X/b/i.py" "$2" "$3" &\nchild=$!\nwhile true; do\n set +e; wait "$child"; rc=$?; set -e\n if kill -0 "$child" 2>/dev/null; then continue; fi\n break\ndone\nexit "$rc"\n'
 # h.forward matches the supervisor's first argument, so X names the case.
 shell=shell.replace('\nX="$1"\n','\nX="$2"\n').replace('"$X/b/i.py"','"$HX/b/i.py"')
 (P/'wrapper.sh').write_text(shell)
 write(P/'SOURCE.json',dict(trap_source='work/tree_r1/launch_s1/b/r.sh',trap_sha256=hashlib.sha256(trap.encode()).hexdigest(),
  admission_scope='CPU proof bypasses allocation/admission setup; native trap, forward, relay and rank loop execute',
  boundary=['tiny randomly initialized native LM and pose heads','tiny pretrained tokenizer/processor; native RGB encoding and SQLite readers'],
  functions=['carrier_c1_run.run_steps','carrier_c1_run.checkpoint','carrier_c1_run.export','carrier_c1_run.load_artifact','launch_s1/b/h.forward','launch_s1/b/i.relay']))
def driver():
 space=os.statvfs('/scratch')
 if space.f_bavail*space.f_frsize<85*1024**3:raise SystemExit('Scratch reserve below the build limit; no proof outputs written')
 P.mkdir(parents=True,exist_ok=True);result=dict(status='FAIL',checks={key:False for key in ('step_one','signal_forwarding','signal_boundary','signal_export','signal_checkpoint','signal_reload','fallback_boundary','fallback_export','fallback_checkpoint','fallback_reload')},end_slots=[],elapsed_seconds=None)
 start=time.monotonic();result['temporary_sizes']=[]
 try:
  setup()
  for case in ('signal','fallback'):
   result['temporary_sizes'].append(dict(case=case,phase='before',bytes=tmp_size()))
   root=P/case;root.mkdir(exist_ok=True)
   write(root/'binding.json',{'fixture':'native-stop'})
   for r in range(2):
    write(root/f'ready_{r}.json',{});write(root/f'signal_{r}.json',{});write(root/f'rank_{r}.json',{})
   write(root/'release.json',{});write(root/'reload.json',{})
   (root/'metrics_cpu.jsonl').write_text('')
   if (root/'request.stop').exists():(root/'request.stop').replace(root/'request.previous')
   # The forwarder requires the exact supervisor path/root pair.
   (root/'b').mkdir(exist_ok=True)
   (root/'b/i.py').write_bytes((P/'b/i.py').read_bytes())
   shell=(P/'wrapper.sh').read_text().replace('"$HX/b/i.py"','"$X/b/i.py"')
   (P/'wrapper.sh').write_text(shell)
   with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
   env={**os.environ,'MASTER_ADDR':'127.0.0.1','MASTER_PORT':str(port),'GLOO_SOCKET_IFNAME':'lo'}
   with (root/'run.log').open('w') as log:
    child=subprocess.Popen(['bash',str(P/'wrapper.sh'),str(P),str(root),case,sys.executable],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    deadline=start+540
    if case=='signal':
     while not all(marked(root/f'ready_{r}.json','next_step') for r in range(2)):
      if child.poll() is not None:raise RuntimeError('Ranks failed before step 1; inspect signal/run.log')
      if time.monotonic()>deadline:raise TimeoutError('rank readiness deadline')
      time.sleep(.2)
     metrics=[json.loads(x) for x in (root/'metrics_cpu.jsonl').read_text().splitlines()]
     assert metrics[-1]['step']==1
     result['checks']['step_one']=True
     os.kill(child.pid,signal.SIGUSR1)
     end=time.monotonic()+10
     while not all(marked(root/f'signal_{r}.json','received') for r in range(2)):
      if time.monotonic()>end:raise TimeoutError('USR1 did not reach both ranks')
      time.sleep(.05)
     result['checks']['signal_forwarding']=True
     write(root/'release.json',dict(signal_received=True))
    code=child.wait(timeout=max(1,deadline-time.monotonic()))
    assert code==0,(case,code)
   last=2 if case=='signal' else 1
   ranks=[json.loads((root/f'rank_{r}.json').read_text()) for r in range(2)]
   result['checks'][case+'_boundary']=all(r['last_step']==last and r['stopped'] for r in ranks)
   reload=json.loads((root/'reload.json').read_text());assert reload['finite']
   result['checks'][case+'_reload']=True
   assert sha(Path(reload['artifact']['path']))==reload['artifact']['sha256']
   result['checks'][case+'_export']=True
   checkpoints=list(root.glob(f'checkpoint_{last:06d}*/complete.json'));assert checkpoints
   checkpoint=max(checkpoints,key=lambda p:p.stat().st_mtime_ns)
   manifest=json.loads(checkpoint.read_text());assert manifest['step']==last
   for name,pin in manifest['files'].items():
    payload=checkpoint.parent/name
    assert payload.stat().st_size==pin['bytes'] and sha(payload)==pin['sha256']
   result['checks'][case+'_checkpoint']=True
   result['end_slots'].append(dict(case=case,export=reload['artifact'],checkpoint=dict(path=str(checkpoint),sha256=sha(checkpoint))))
   result['temporary_sizes'].append(dict(case=case,phase='after',bytes=tmp_size()))
  result['status']='PASS'
 except Exception as e:
  if 'child' in locals() and child.poll() is None:
   os.killpg(child.pid,signal.SIGTERM)
   child.wait(timeout=20)
  result.update(error=type(e).__name__+': '+str(e),traceback=traceback.format_exc(),next_action='lane runs RUN.sh after build 8')
 finally:
  result['elapsed_seconds']=time.monotonic()-start
  result['bytes']=sum(p.stat().st_size for p in P.rglob('*') if p.is_file())
  result['checks']['size_limit']=result['bytes']<500_000_000
  result['checks']['time_limit']=result['elapsed_seconds']<600
  if not all(result['checks'].values()):result['status']='FAIL'
  write(P/'RESULT.json',result)
 print(json.dumps(result));raise SystemExit(0 if result['status']=='PASS' and all(result['checks'].values()) else 1)
if __name__=='__main__':
 mode=sys.argv[1] if len(sys.argv)>1 else 'driver'
 if mode=='rank':
  sys.path.insert(0,str(Path(__file__).parent))
  from stop_monitor import Monitor
  monitor=Monitor(T,Path(sys.argv[2])/('coverage_rank_'+os.environ['RANK']));complete=False
  try:rank(Path(sys.argv[2]),sys.argv[3]);complete=True
  finally:monitor.finish(complete)
 elif mode=='supervise':supervise(Path(sys.argv[2]),sys.argv[3])
 else:driver()
