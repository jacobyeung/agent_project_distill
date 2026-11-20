# kit/b/a.py

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 47 launch lines removed; 10 rehearsal lines added. Functions: launch <module>, refused; rehearsal <module>.

```diff

--- launch/kit/b/a.py
+++ run4/kit/b/a.py
@@ -6,24 +6,13 @@
  if hashlib.sha256(r).hexdigest()!=v['sha256']:raise ValueError('E01')
  return json.loads(r)
 kit=Path(__file__).resolve().parents[1];control=read(kit/'k/a.json')
-if len(sys.argv) not in (3,4) or sys.argv[1] not in ('p','t','q','r'):raise ValueError('E02')
-if (sys.argv[1] in ('q','r')) != (len(sys.argv)==4):raise ValueError('E02')
+if len(sys.argv) not in (3,4) or sys.argv[1] not in ('p','t','q'):raise ValueError('E02')
+if (sys.argv[1]=='q') != (len(sys.argv)==4):raise ValueError('E02')
 if sys.argv[1]=='t' and control['GO'] is not True:raise ValueError('E03')
 root=Path(sys.argv[2]).resolve()
 if root==Path('/tmp') or not root.is_relative_to(Path('/tmp')):raise ValueError('E06')
 if root.exists() and any(root.iterdir()):raise ValueError('E04')
 root.mkdir(parents=True,mode=0o700,exist_ok=True)
-if sys.argv[1] in ('q','r'):
- import os
- sys.path.insert(0,str(kit/'b'))
- from z import screen,write,load
- def refused(kind,value,traceback):
-  text=screen(kind.__name__+':'+str(value),read(kit/'k/g.json'),load(kit/'b/wh.json'))
-  write(root/'r0.json',dict(status='REFUSE',refusal=text[:100000]))
-  sys.__excepthook__(kind,value,traceback)
- sys.excepthook=refused
- job=os.environ.get('SLURM_JOB_ID','')
- if not job.isascii() or not job.isdigit():raise ValueError('R1_ROUTING_JOB_ID_REQUIRED')
 src=control['source'];p=kit/src['path']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=src['sha256']:raise ValueError('E05')
 with tarfile.open(p) as t:t.extractall(root/'s',filter='data')
@@ -37,43 +26,17 @@
  result = original_host(cfg, directory, request, job_tmp_token=job_tmp_token)
  host_write(root/'host.json',result)
  return result
-if sys.argv[1]=='p':host_entry.frame_host = recorded_host
-if sys.argv[1] in ('q','r'):
+host_entry.frame_host = recorded_host
+if sys.argv[1]=='q':
+ from launch_r1.production_proof import run
  from student_pilot.p3_provenance import load
+ request=load(sys.argv[3])
  from student_pilot.r1_persisted import scope
  sys.path.insert(0,str(kit/'b'))
- from pl import plan_payload
- from z import write
- mode=sys.argv[1];incoming=load(sys.argv[3])
- if '_resolved' not in incoming:raise ValueError('R1_STAGING_PLAN_REQUIRED')
- request,paths,stage=plan_payload(kit,incoming['_resolved'],root,regeneration=mode=='r')
- with scope(paths):
-  try:
-   if mode=='q':
-    from launch_r1.production_proof import run
-    r=run(request,root/'q',stage=stage)
-    if r['status']=='ADMIT':
-     from cs import publish
-     from student_pilot.p3_provenance import pinned
-     publish(kit,root.parent,load(pinned(r['config'])),os.environ['SLURM_JOB_ID'])
-   else:
-    import os,shutil
-    from launch_r1.entry import begin_host,host_environment,check_host_runtime,stage_host,check_host_scene
-    from student_pilot.p3_provenance import pinned
-    cfg=load(pinned(request['config']))
-    directory,job_tmp,host=begin_host(cfg,root/'q',request)
-    with host_environment(job_tmp):
-     check_host_runtime(cfg,request,host)
-     cfg=stage_host(cfg,directory,request,job_tmp,stage=stage)
-     check_host_scene(cfg,host)
-     from rg import regenerate
-     regenerate(cfg,directory)
-    r={'status':'ADMIT'}
-  finally:stage.close()
- # d.py reads only the fully planned, authenticated configuration.
- request['_paths']=paths
- write(root.parent/'r.json',request)
- write(root.parent/'n.json',load(root/'plan.json')['config'])
+ from i import refresh
+ with scope(request.pop('_paths',{})):
+  request=refresh(request,root/'i')
+  r=run(request,root/'q')
  print(json.dumps({'ok':r['status']=='ADMIT'}))
  sys.exit(0 if r['status']=='ADMIT' else 1)
 from launch_r1.entry import frame_host,admit,create_job_tmp

```

run5: 15 launch lines removed; 4 rehearsal lines added. Functions: launch <module>, refused; rehearsal <module>.

```diff

--- launch/kit/b/a.py
+++ run5/kit/b/a.py
@@ -13,17 +13,6 @@
 if root==Path('/tmp') or not root.is_relative_to(Path('/tmp')):raise ValueError('E06')
 if root.exists() and any(root.iterdir()):raise ValueError('E04')
 root.mkdir(parents=True,mode=0o700,exist_ok=True)
-if sys.argv[1] in ('q','r'):
- import os
- sys.path.insert(0,str(kit/'b'))
- from z import screen,write,load
- def refused(kind,value,traceback):
-  text=screen(kind.__name__+':'+str(value),read(kit/'k/g.json'),load(kit/'b/wh.json'))
-  write(root/'r0.json',dict(status='REFUSE',refusal=text[:100000]))
-  sys.__excepthook__(kind,value,traceback)
- sys.excepthook=refused
- job=os.environ.get('SLURM_JOB_ID','')
- if not job.isascii() or not job.isdigit():raise ValueError('R1_ROUTING_JOB_ID_REQUIRED')
 src=control['source'];p=kit/src['path']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=src['sha256']:raise ValueError('E05')
 with tarfile.open(p) as t:t.extractall(root/'s',filter='data')
@@ -52,10 +41,6 @@
    if mode=='q':
     from launch_r1.production_proof import run
     r=run(request,root/'q',stage=stage)
-    if r['status']=='ADMIT':
-     from cs import publish
-     from student_pilot.p3_provenance import pinned
-     publish(kit,root.parent,load(pinned(r['config'])),os.environ['SLURM_JOB_ID'])
    else:
     import os,shutil
     from launch_r1.entry import begin_host,host_environment,check_host_runtime,stage_host,check_host_scene
@@ -68,6 +53,10 @@
      check_host_scene(cfg,host)
      from rg import regenerate
      regenerate(cfg,directory)
+    spec=read(kit/'k/p.json');job=os.environ.get('SLURM_JOB_ID','')
+    if not job.isdigit():raise ValueError('R1_ROUTING_JOB_ID_REQUIRED')
+    destination=Path(spec['n_root'])/'o'/job;destination.mkdir(parents=True,exist_ok=True,mode=0o700)
+    shutil.copyfile(root/'routing_selection.json',destination/'routing_selection.json')
     r={'status':'ADMIT'}
   finally:stage.close()
  # d.py reads only the fully planned, authenticated configuration.

```
