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
def tb_write(where,error):return None
if sys.argv[1] in ('q','r'):
 import os
 sys.path.insert(0,str(kit/'b'))
 from z import screen,write,load
 def tb_write(where,error):
  # Append the full, unscreened traceback of an exception to the node-local file beside r.json:
  # once per exception, at most 65536 bytes a record and 204800 bytes in all. Never raises.
  try:
   import time,traceback
   if getattr(error,'_tb_written',False):return None
   try:error._tb_written=True
   except Exception:pass
   text='=== %s pid=%d where=%s %s\n'%(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),os.getpid(),where,type(error).__name__)
   text+='Stack above the wrapper:\n'+''.join(traceback.format_stack()[:-1])
   text+=''.join(traceback.format_exception(type(error),error,error.__traceback__))+'\n'
   data=text.encode('utf-8','replace')
   if len(data)>65536:data=data[:16384]+data[-49152:]
   path=root.parent/'tb.txt'
   room=204800-(path.stat().st_size if path.exists() else 0)
   if room>0:
    descriptor=os.open(path,os.O_WRONLY|os.O_APPEND|os.O_CREAT,0o600)
    try:os.write(descriptor,data[:room])
    finally:os.close(descriptor)
  except Exception:pass
  return None
 def refused(kind,value,traceback):
  tb_write('uncaught',value)
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
from launch_r1 import entry as host_entry
from student_pilot.p3_provenance import write as host_write
original_selection = host_entry.check_host_selection
def guarded_selection(cfg, directory, request, result, *, record=False):
 try:
  from rb import routing_status
  routing_status(cfg)
  return original_selection(cfg, directory, request, result, record=record)
 except BaseException as error:tb_write('selection',error);raise
host_entry.check_host_selection = guarded_selection
original_host = host_entry.frame_host
def recorded_host(cfg, directory, request, *, job_tmp_token=None):
 try:
  result = original_host(cfg, directory, request, job_tmp_token=job_tmp_token)
  host_write(root/'host.json',result)
  return result
 except BaseException as error:tb_write('host',error);raise
if sys.argv[1]=='p':host_entry.frame_host = recorded_host
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
    # admit() lowers the soft RLIMIT_AS for its CPU-only work and never restores it; the same
    # process later opens the device for the forward, so restore the earlier limit on return.
    import resource
    import student_pilot.s1_admission as admission_module
    native_admit=admission_module.admit
    # A driver query made while admit() hides the devices would leave a process that has not opened
    # a device unable to open one later; b/mg.py answers the device queries without the driver while
    # the mask is empty and the library is not initialized. A process that opened a device before the
    # mask keeps it under the mask, and there the library's own functions answer.
    from mg import guard
    def restoring_admit(*args,**kwargs):
     limit=resource.getrlimit(resource.RLIMIT_AS)
     try:
      # The proof runs under the namespace, where every reviewed path string was written. The frame root
      # map may only name the job folder under /tmp/jjyeung, and the frame audit compares resolved paths,
      # so admit() gets the request's frame roots under that second name (b/pf.py audit_roots: the same
      # directories, or the job refuses by name).
      from pf import audit_roots
      if len(args)>2:args=(*args[:2],audit_roots(args[2]),*args[3:])
      else:kwargs['roots']=audit_roots(kwargs['roots'])
      with guard():return native_admit(*args,**kwargs)
     except BaseException as error:tb_write('admit',error);raise
     finally:resource.setrlimit(resource.RLIMIT_AS,limit)
    admission_module.admit=restoring_admit
    # The forward runs in this process, as the tree runs it. _run turns the exception of any step
    # into its refusal text with str(error); this name records that exception's traceback first.
    import launch_r1.production_proof as proof_module
    def refusal_text(*args,**kwargs):
     if args and isinstance(args[0],BaseException):tb_write('refusal',args[0])
     return str(*args,**kwargs)
    proof_module.str=refusal_text
    from launch_r1.production_proof import run
    r=run(request,root/'q',stage=stage)
    if r['status']=='ADMIT':
     from cs import publish
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
