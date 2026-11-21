# Copy of the kit's b/u.py (seal, GO, RESULT, identity, verify_staging, admit, train) for the rehearsal.
# Differences: the kit is $Q_KIT; train(cfg, smoke_steps=A15_STEPS) (the tree's own two-step length) in
# place of the full schedule; every stage and optimizer step is timed into $A15_LOG/ev_rank<r>.jsonl
# (wrappers log and re-raise, they change no value); A15_DRY=1 (Trinity test only) stops after the tree's
# authenticate() under the layout, before anything needs a GPU.
import sys,os,json,time,traceback,importlib,math,functools
from pathlib import Path
RANK=os.environ.get('RANK','x');EV=Path(os.environ['A15_LOG'])/('ev_rank%s.jsonl'%RANK)
def ev(kind,**kw):
 rec=dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),t=round(time.time(),3),rank=RANK,kind=kind,**kw)
 with open(EV,'a') as f:f.write(json.dumps(rec,default=str)+'\n')
def err(where,e):ev('ERROR',where=where,type=type(e).__name__,message=str(e)[:4000],traceback=traceback.format_exc()[-12000:])
def timed(name,fn):
 @functools.wraps(fn)
 def w(*a,**k):
  t=time.time();ev('BEGIN',stage=name)
  try:r=fn(*a,**k)
  except BaseException as e:err(name,e);raise
  ev('END',stage=name,seconds=round(time.time()-t,3));return r
 return w
ev('START',pid=os.getpid(),cvd=os.environ.get('CUDA_VISIBLE_DEVICES'),world=os.environ.get('WORLD_SIZE'),local_rank=os.environ.get('LOCAL_RANK'),
   master=os.environ.get('MASTER_ADDR','')+':'+os.environ.get('MASTER_PORT',''),omp=os.environ.get('OMP_NUM_THREADS'),argv=sys.argv[1:])
try:
 k=Path(os.environ['Q_KIT']).resolve();sys.path.insert(0,str(k/'b'))
 from z import load,seal
 seal(k)
 if load(k/'k/a.json')['GO'] is not True:raise ValueError('E03')
 r=Path(sys.argv[1]);q=load(r/'q/RESULT.json')
 if q.get('status')!='ADMIT' or q.get('init_milestone')!=400:raise ValueError('E81')
 sys.path.insert(0,str(r/'s'))
 PK=bytes.fromhex('73747564656e745f70696c6f74').decode()
 prov=importlib.import_module(PK+'.p3_provenance');read,pinned=prov.load,prov.pinned
 C=importlib.import_module(PK+'.carrier_c1_run');identity,train=C.identity,C.train
 scope=importlib.import_module(PK+'.r1_persisted').scope
 cfg=read(sys.argv[2]);before=read(pinned(q['config']))
 if identity(cfg)!=identity(before) or cfg['world_size']!=4:raise ValueError('E82')
 ev('CHECKED',identity=identity(cfg),tree=str(Path(C.__file__)),tree_is_link=any(p.is_symlink() for p in Path(C.__file__).parents))
 import launch_r1.entry as E
 import launch_r1.production_proof as PP
 request=load(r.parent/'r.json')
 if os.environ.get('A15_DRY') in ('1','sleep'):
  with scope(request.get('_paths',{})),scope(cfg['r1_training']['persisted_files']):
   commit=timed('authenticate',C.authenticate)(cfg)
  ev('DRY_DONE',authenticate=commit)
  if os.environ['A15_DRY']=='sleep':time.sleep(600)
  sys.exit(0)
 for name in ('prepared','authenticate','load_model','fla_check','network_preflight','wrap_model','run_steps'):
  setattr(C,name,timed(name,getattr(C,name)))
 native=C.optimize_step
 def step(*a,**kw):
  t=time.time();n=a[6] if len(a)>6 else kw.get('step');ev('STEP_BEGIN',step=n)
  try:info,extra=native(*a,**kw)
  except BaseException as e:err('optimize_step',e);raise
  sm=info.get('stream_means',{})
  ev('STEP',step=n,seconds=round(time.time()-t,3),wall_seconds=info.get('wall_seconds'),stream_means=sm,
     finite=all(isinstance(v,(int,float)) and math.isfinite(v) for v in sm.values()),components=info.get('components'),
     peak_allocated_gib=round(info.get('peak_allocated_bytes',0)/2**30,2),peak_reserved_gib=round(info.get('peak_reserved_bytes',0)/2**30,2),
     skipped=info.get('skipped_microsteps'))
  return info,extra
 C.optimize_step=step
 E.admit=timed('admit',E.admit)
 with scope(request['_paths']),scope(cfg['r1_training']['persisted_files']):
  timed('verify_staging',PP.verify_staging)(request)
  E.admit(cfg)
  report=timed('train',train)(cfg,smoke_steps=int(os.environ.get('A15_STEPS','2')))
 ev('TRAIN_RETURNED',status=(report or {}).get('status') if isinstance(report,dict) else None)
except SystemExit:raise
except BaseException as e:
 err('u2',e);raise
