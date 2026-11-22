import base64,hashlib,json,os,sys,tarfile,tempfile
from pathlib import Path
# Whole-leg disk plan check. The counts come from the tree's own checkpoint_space.plan and Budget on the job's
# configuration; the bytes use the formulas of checkpoint_space.check (state 5/4 of the measured optimizer-state
# tensors, export 10/4 of the exported tensors, 64 MiB allowance, 10240 B per archive copy). The measured tensor bytes
# (M, X below) are the pair that reproduces the guard of job 174246 exactly: 6,027,674,886,604 B for 16 states and
# 7 exports with one archive copy. Free space is read like check(): statvfs of the output folder's nearest existing
# ancestor. Refuses unless free exceeds the plan by the bar.
# Usage: dp.py preflight <kit> <probe dir> <bar bytes>          (kit config k/c.json, tree from the kit's sealed tar)
#        dp.py train <kit> <probe dir or - for the config's output> <bar bytes> <v.json> <tree dir>  (job config, job's tree)
M=110_246_315_968;X=40_421_000_132;MIB64=64*1024**2
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capsule(p):
 v=json.loads(Path(p).read_text());r=base64.b64decode(v['payload'],validate=True)
 if hashlib.sha256(r).hexdigest()!=v['sha256']:raise ValueError('E01')
 return json.loads(r)
def refuse(code,**detail):
 print(json.dumps(dict(event='disk_plan',status='REFUSE',code=code,**detail)),flush=True);raise SystemExit(3)
def required(policy,Budget):
 b=Budget(policy);states,exports=b.remaining('checkpoint')
 S=(M*5+3)//4+MIB64;E=(X*10+3)//4+MIB64
 native=states*S+exports*E
 archive=b.policy.get('retained_archive_copies',0)*(states*(S+10240)+exports*(E+10240))
 return states,exports,S,E,native+archive+b.policy['reserve_bytes']
def run(mode,kit,probe,bar,cfg,tree):
 sys.path.insert(0,str(tree))
 from student_pilot.checkpoint_space import plan,Budget
 from student_pilot.carrier_c1_sweep import recipe_for
 import student_pilot.checkpoint_space as cs
 if not Path(cs.__file__).resolve().is_relative_to(Path(tree).resolve()):refuse('DISK_PLAN_TREE_PATH',reason='tree import path')
 recipe=recipe_for(cfg);expected=plan(recipe,retained_archive_copies=1)
 if cfg.get('checkpoint_disk_guard')!=expected:refuse('R1_DISK_PLAN_DIFFERS',reason='R1_DISK_PLAN_DIFFERS',config=cfg.get('checkpoint_disk_guard'),plan=expected)
 ref=dict(planned_full_states=14,extra_full_states=2,planned_weight_exports=7,reserve_bytes=200_000_000_000,retained_archive_copies=1)
 if required(ref,Budget)[4]!=6_027_674_886_604:refuse('DISK_PLAN_ARITHMETIC',reason='byte arithmetic does not reproduce 174246')
 states,exports,S,E,need=required(expected,Budget)
 path=Path(cfg['output'] if probe=='-' else probe).resolve()
 while not path.exists() and path!=path.parent:path=path.parent
 u=os.statvfs(path);free=u.f_bavail*u.f_frsize
 rec=dict(event='disk_plan',mode=mode,probe=str(path),free_bytes=free,plan_bytes=need,bar_bytes=bar,margin_bytes=free-need,
          states=states,exports=exports,state_bytes=S,export_bytes=E,policy=expected,milestones=recipe['milestones'])
 if free<=need+bar:refuse('DISK_PLAN_INSUFFICIENT',**{k:v for k,v in rec.items() if k!='event'})
 print(json.dumps(dict(rec,status='PASS')),flush=True)
if len(sys.argv)<5 or sys.argv[1] not in ('preflight','train'):refuse('DISK_PLAN_USAGE',reason='usage')
mode,kit,probe,bar=sys.argv[1],Path(sys.argv[2]),sys.argv[3],int(sys.argv[4])
if bar<0:refuse('DISK_PLAN_USAGE',reason='bar')
if mode=='train':
 if len(sys.argv)!=7:refuse('DISK_PLAN_USAGE',reason='usage')
 run(mode,kit,probe,bar,json.loads(Path(sys.argv[5]).read_text()),Path(sys.argv[6]))
else:
 if len(sys.argv)!=5:refuse('DISK_PLAN_USAGE',reason='usage')
 control=capsule(kit/'k/a.json');src=control['source'];tar=kit/src['path']
 if sha(tar)!=src['sha256']:refuse('DISK_PLAN_TREE_DIFFERS',reason='tree tar differs from its pin')
 with tempfile.TemporaryDirectory(prefix='dp_') as t:
  with tarfile.open(tar) as a:a.extractall(Path(t)/'s',filter='data')
  run(mode,kit,probe,bar,capsule(kit/'k/c.json'),Path(t)/'s')
