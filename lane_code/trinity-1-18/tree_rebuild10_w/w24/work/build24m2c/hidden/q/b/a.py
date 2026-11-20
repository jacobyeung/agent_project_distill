import base64,hashlib,json,sys,tarfile
from pathlib import Path
if sys.version_info < (3,12):raise RuntimeError('Python 3.12 or newer required')
def read(p):
 v=json.loads(p.read_text());r=base64.b64decode(v['payload'],validate=True)
 if hashlib.sha256(r).hexdigest()!=v['sha256']:raise ValueError('E01')
 return json.loads(r)
kit=Path(__file__).resolve().parents[1];control=read(kit/'k/a.json')
if len(sys.argv) not in (3,4) or sys.argv[1] not in ('p','t','q','r'):raise ValueError('E02')
if (sys.argv[1] in ('q','r')) != (len(sys.argv)==4):raise ValueError('E02')
if sys.argv[1]=='t' and control['GO'] is not True:raise ValueError('E03')
root=Path(sys.argv[2]).resolve()
if root==Path('/tmp') or not root.is_relative_to(Path('/tmp')):raise ValueError('E06')
if root.exists() and any(root.iterdir()):raise ValueError('E04')
root.mkdir(parents=True,mode=0o700,exist_ok=True)
if sys.argv[1] in ('q','r'):
 import os
 sys.path.insert(0,str(kit/'b'))
 from z import screen,write,load
 def refused(kind,value,traceback):
  text=screen(kind.__name__+':'+str(value),read(kit/'k/g.json'),load(kit/'b/wh.json'))
  write(root/'r0.json',dict(status='REFUSE',refusal=text[:100000]))
  sys.__excepthook__(kind,value,traceback)
 sys.excepthook=refused
 job=os.environ.get('SLURM_JOB_ID','')
 if not job.isascii() or not job.isdigit():raise ValueError('R1_ROUTING_JOB_ID_REQUIRED')
src=control['source'];p=kit/src['path']
if hashlib.sha256(p.read_bytes()).hexdigest()!=src['sha256']:raise ValueError('E05')
with tarfile.open(p) as t:t.extractall(root/'s',filter='data')
sys.path.insert(0,str(root/'s'))
from launch_r1.build import verify
verify(kit)
if sys.argv[1] in ('q','r'):
 from student_pilot.p3_provenance import load
 from student_pilot.r1_persisted import scope
 sys.path.insert(0,str(kit/'b'))
 from pl import plan_payload
 from z import write
 mode=sys.argv[1];incoming=load(sys.argv[3])
 if '_resolved' not in incoming:raise ValueError('R1_STAGING_PLAN_REQUIRED')
 request,paths,stage=plan_payload(kit,incoming['_resolved'],root,regeneration=mode=='r')
 with scope(paths):
  try:
   if mode=='q':
    from launch_r1.production_proof import run
    r=run(request,root/'q',stage=stage)
    if r['status']=='ADMIT':
     from sv import publish
     from student_pilot.p3_provenance import pinned
     publish(kit,root.parent,load(pinned(r['config'])),os.environ['SLURM_JOB_ID'])
   else:
    import os,shutil
    from launch_r1.entry import begin_host,host_environment,check_host_runtime,stage_host,check_host_scene
    from student_pilot.p3_provenance import pinned
    cfg=load(pinned(request['config']))
    directory,job_tmp,host=begin_host(cfg,root/'q',request)
    with host_environment(job_tmp):
     check_host_runtime(cfg,request,host)
     cfg=stage_host(cfg,directory,request,job_tmp,stage=stage)
     check_host_scene(cfg,host)
     from rg import regenerate
     regenerate(cfg,directory)
    r={'status':'ADMIT'}
  finally:stage.close()
 # d.py reads only the fully planned, authenticated configuration.
 request['_paths']=paths
 write(root.parent/'r.json',request)
 write(root.parent/'n.json',load(root/'plan.json')['config'])
 print(json.dumps({'ok':r['status']=='ADMIT'}))
 sys.exit(0 if r['status']=='ADMIT' else 1)
from launch_r1.entry import frame_host,admit,create_job_tmp
cfg=read(kit/'k/c.json')
if sys.argv[1]=='p':
 request=read(kit/'k/h.json')
 job_tmp=root/'j'
 token=create_job_tmp(job_tmp)
 request['job_tmp']=str(job_tmp)
 r=frame_host(cfg,job_tmp/'p',request,job_tmp_token=token)
 print(json.dumps({'ok':r['status']=='PASS'}))
 sys.exit(0 if r['status']=='PASS' else 1)
admit(cfg)
from student_pilot.carrier_c1_run import train
train(cfg)
