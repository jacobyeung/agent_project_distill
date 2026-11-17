# Source comparison

No implementation source was changed. No replacement `0.tgz` was built. The stop condition and outstanding work are in `REPORT.md`.

`PRODUCTION_SOURCE_SHA256.json` lists the SHA256 and byte count of every member of the authoritative production archive alongside the extracted `out/src/` copy. All 924 members match. This proves extraction identity only; it is not a comparison with a new package.

`KIT_COMPARISON.json` compares every supplied builder-tree file with its corresponding production member. The Python source differences are confined to `job.py`, `operator.py`, and `runner.py`. Documentation and registry files absent from the payload are marked explicitly.

The production job validates ordered type selections, creates namespace mount roots before preparation, and forwards selected types. Its operator includes `/usr/local/bin` in PATH. Its runner limits phase execution, completion accounting, journal identity, and timing samples to selected types.

Every changed line from the builder Python snapshot to production follows. Production is authoritative.

```diff
--- in/kit_src_3_30/job.py
+++ out/production/orchard_h10/job.py
@@ -10,7 +10,7 @@
 import tarfile
 import time
 
-from orchard_h10.common import canonical, sha, template, write, opaque, checked_run, read_config
+from orchard_h10.common import ORDER, canonical, sha, template, write, opaque, checked_run, read_config
 
 
 def verify_config(cfg):
@@ -22,6 +22,12 @@
     """Fail closed until every unresolved archive and dependency has a full pin."""
     import re
     valid=lambda value:isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value)
+    if 'types' in inputs:
+        types=inputs['types']
+        if (not isinstance(types,list) or not types
+                or any(not isinstance(kind,str) or kind not in ORDER for kind in types)
+                or types!=[kind for kind in ORDER if kind in types]):
+            raise ValueError('Invalid type selection')
     if inputs.get('schema')!=1 or not inputs.get('archives'):raise ValueError('Unresolved input archives')
     for a in inputs['archives']:
         if not valid(a.get('sha256')) or not a.get('parts') or a.get('expanded_bytes',0)<=0:
@@ -161,6 +167,7 @@
         stage(root,cfg,inputs,S,J)
         write(root/'1.json',inputs)
         if time.time()>=end-cfg['stop_margin'] or (out/'metadata/STOP').exists():raise ValueError('No read budget after staging')
+        for name in ('sj','fsw','m/ap'):(root/name).mkdir(parents=True,exist_ok=True)
         env=J.environment(root)
         p=cfg['logical']+'/p'
         env={k:v for k,v in env.items() if 'sam' not in k.lower()}
@@ -178,6 +185,7 @@
                      export=cfg['logical']+'/d/e',binding=cfg['logical']+'/d/binding.json',
                      settings=cfg['logical']+'/d/settings.json',plan_sha256=cfg['plan_sha256'],
                      inputs_sha256=canonical({k:v for k,v in inputs.items() if k!='resume'}),
+                     types=inputs.get('types') or list(ORDER),
                      stop_margin=cfg['stop_margin'],return_margin=cfg['return_margin'],
                      prefix=['bash',inputs['policy']['vnice']])
         if inputs.get('optional'):
--- in/kit_src_3_30/operator.py
+++ out/production/orchard_h10/operator.py
@@ -70,7 +70,7 @@
     export=f"--export=A_N={gpus},A_T={seconds(walltime)},A_I={digest(package/'a/1.json')},A_C={digest(package/'2.json')}"
     argv[argv.index('--export=NONE')]=export
     opaque(argv)
-    env={'PATH':'/usr/bin:/bin','HOME':os.environ['HOME'],'USER':os.environ['USER']}
+    env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':os.environ['HOME'],'USER':os.environ['USER']}
     opaque([f'{k}={v}' for k,v in env.items()])
     body=(package/'BATCH.sh').read_bytes()
     # Check retained package pins again; no implicit check+submit retry chain.
--- in/kit_src_3_30/runner.py
+++ out/production/orchard_h10/runner.py
@@ -95,7 +95,8 @@
     from h1eval.cli import modes
     items=load_manifest(config.get('items',Path(config['package'])/'items/devs1_routed.json'))['items']
     root=Path(config['output'])/'metadata/journals';counts=[]
-    for t,kind in enumerate(ORDER):
+    for kind in config.get('types') or list(ORDER):
+        t=ORDER.index(kind)
         for i in range(len(cards)):
             chosen=select_types(items,selected(items,f'{i}/{len(cards)}'),kind)
             expected=plan(chosen,['own'],[{'name':'none'},*modes(DEFAULT_MODES)])
@@ -118,7 +119,8 @@
 def run(config, cards, end_time, *, prefix=(), clock=time.time, launcher=subprocess.Popen):
     if not 1 <= len(cards) <= 4 or len(set(cards))!=len(cards):raise ValueError('Require 1–4 distinct assigned cards')
     out=Path(config['output']);(out/'metadata').mkdir(parents=True,exist_ok=True);(out/'logs').mkdir(exist_ok=True)
-    identity=dict(plan=config['plan_sha256'],inputs=config.get('inputs_sha256'),cards=len(cards),order=list(ORDER),arms=['own'])
+    types=config.get('types') or list(ORDER)
+    identity=dict(plan=config['plan_sha256'],inputs=config.get('inputs_sha256'),cards=len(cards),order=list(ORDER),types=types,arms=['own'])
     identity_path=out/'metadata/IDENTITY.json'
     if identity_path.exists() and json.loads(identity_path.read_text())!=identity:
         raise ValueError('Resume requires the same plan and GPU shard count')
@@ -131,7 +133,8 @@
     old={n:signal.signal(n,stop) for n in (signal.SIGUSR1,signal.SIGTERM,signal.SIGINT)}
     failure=None
     try:
-        for t,kind in enumerate((*ORDER,*(['optional'] if optional_ready(config) else []))):
+        for kind in (*types,*(['optional'] if optional_ready(config) else [])):
+            t=ORDER.index(kind) if kind in ORDER else len(ORDER)
             if clock()>=stop_at or marker.exists():break
             processes=[]
             with ExitStack() as stack:
@@ -160,8 +163,10 @@
         # Aggregate measured timing even when no shard has reached ten reads yet.
         from h1eval.h10.launch import read_records
         samples=[]
-        for path in sorted((out/'metadata/journals').glob('*/*/items.jsonl')):
-            samples.extend(r['seconds'] for r in read_records(path))
+        for kind in (*types,*(['optional'] if optional_ready(config) else [])):
+            t=ORDER.index(kind) if kind in ORDER else len(ORDER)
+            for path in sorted((out/'metadata/journals'/str(t)).glob('*/items.jsonl')):
+                samples.extend(r['seconds'] for r in read_records(path))
         write(out/'metadata/projection.json',dict(sample_reads=len(samples),
             seconds_per_read=sum(samples)/len(samples) if samples else None,
             projected_gpu_hours=summary['expected']*sum(samples)/len(samples)/3600 if samples else None,
```

The vendored export stager differs from the supplied reviewed stager. Both `stage_export` and `parse_done` have identical function text, but their run registry differs. The supplied fetch function also imports an external `binding` module and consumes a configured export binding and optional claim. Copying that whole module without its dependencies would not be a drop-in integration.

Production stager SHA256: `8c926e7c21663e7d707c7bc4adf1a2a9d73202e397e1531ef08ec3cadee859ed`.

Supplied stager SHA256: `f8a790f693baf0b9997dfbb84fb2811975b406b30db58237c0950138bdc196f3`.

Every changed stager line follows.

```diff
--- out/production/orchard_h10/vendor/export_stage.py
+++ in/h1read_export_stage.py
@@ -15,6 +15,7 @@
 import orchard_stage as S
 import orchard_job as J
 import chain_save as A
+import binding as B
 
 CHECKER = J.SJ/'orch_cd/legs1_reads/out/export_check.py'
 CHECKER_PINS = {
@@ -37,13 +38,13 @@
 
 
 def logical_artifact(root, path, step):
-    allowed = {str(J.FSW/'ap/8865619b/runs'/run/('m'+str(step))/'artifact.json') for run in ('469ddece', '359fcc3c')}
+    allowed = {str(J.FSW/'ap/8865619b/runs'/run/('m'+str(step))/'artifact.json') for run in ('359fcc3c', '17c4ffa4')}
     if path not in allowed or type(step) is not int or step <= 0:
         raise ValueError('Export lineage differs')
     return path
 
 
-T = NS(writable=writable, EXPORT_RUNS=('469ddece', '359fcc3c'),
+T = NS(writable=writable, EXPORT_RUNS=('359fcc3c', '17c4ffa4'),
        FSW=J.FSW, logical_artifact=logical_artifact, physical=J.physical,
        load=lambda p: json.loads(Path(p).read_text()), sha=S.sha, lock=lock,
        kit_stage=lambda: S, dump=A.atomic_json)
@@ -180,11 +181,19 @@
 def fetch_and_stage(root, config):
     root = Path(root)
     step = config['spec']['step']
-    receipt = Path('/project/community/jjyeung/okh7/x_f5c353f7/o')/('gcs_359fcc3c_m'+str(step)+'.done')
+    bound = B.validate(config['spec']['export_binding'])
+    if step != bound['step']: raise ValueError('Export step differs')
+    receipt = Path(bound['done'])
     if receipt.is_symlink() or receipt.stat().st_size > 65536:
         raise ValueError('Invalid completion receipt')
     raw = receipt.read_bytes()
-    done = parse_done(raw, '359fcc3c', step)
+    claim = None
+    if bound['claim']:
+        p = Path(bound['claim'])
+        if p.is_symlink() or p.stat().st_size > 64: raise ValueError('Invalid stop claim')
+        claim = p.read_bytes()
+    done = (parse_done(raw, bound['run'], step) if bound['run']=='359fcc3c'
+            else B.parse(raw, bound, claim))
     uri = 'gs://cmu-gpucloud-jjyeung/'+done['object']
     (root/'archives/COMPLETE.done').write_bytes(raw)
     target = root/'archives/export.tar'
@@ -212,7 +221,7 @@
     local_done = root/'archives/COMPLETE.json'
     A.atomic_json(local_done, done)
     transfer_seconds = time.monotonic()-started
-    result = stage_export(NS(root=str(root), run='359fcc3c', step=step, tar=str(target),
+    result = stage_export(NS(root=str(root), run=bound['run'], step=step, tar=str(target),
                              done=str(local_done), full=True, bwrap=str(root/'bwrap')))
     result['transfer_seconds'] = transfer_seconds
     result['transfer_and_admission_seconds'] = time.monotonic()-started
```
