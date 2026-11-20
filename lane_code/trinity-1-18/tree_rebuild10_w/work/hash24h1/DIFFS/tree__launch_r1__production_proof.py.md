# tree/launch_r1/production_proof.py

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 27 launch lines removed; 9 rehearsal lines added. Functions: launch <module>, _run, run; rehearsal <module>, _run, run.

```diff

--- launch/tree/launch_r1/production_proof.py
+++ run4/tree/launch_r1/production_proof.py
@@ -1,6 +1,5 @@
 """Unsubmitted CPU preparation, persisted handover and full-forward proof."""
 from collections import defaultdict
-from contextlib import ExitStack
 from pathlib import Path
 import argparse
 import resource
@@ -61,11 +60,10 @@
     return file_pin(root/'config.json')
 
 
-def _run(request, output, *, stage=None):
+def _run(request, output):
     """Native admission performs build, composition and prepare in that order."""
-    root = Path(output).resolve()
+    root = Path(output); root.mkdir(parents=True, exist_ok=True)
     result = dict(status='REFUSE',GO=False,steps=[],forward='not requested')
-    environment = ExitStack()
     try:
         result['staged'] = verify_staging(request)
         cfg = load(pinned(request['config']))
@@ -86,14 +84,6 @@
         import os
         if os.uname().nodename.startswith('trinity'):
             raise ValueError('R1_PROOF_FRAME_HOST_REQUIRED')
-        from .entry import (begin_host, host_environment, check_host_runtime, stage_host,
-                            check_host_scene, check_host_selection, finish_host)
-        root, job_tmp, host = begin_host(cfg, root, request)
-        environment.enter_context(host_environment(job_tmp))
-        check_host_runtime(cfg, request, host)
-        cfg = stage_host(cfg, root, request, job_tmp, stage=stage, result=host)
-        check_host_scene(cfg, host, record=True)
-        check_host_selection(cfg, root, request, host, record=True)
         if cfg['r1_training'].get('direction_twins'):
             from student_pilot.r1_direction_twins import augment
             from student_pilot.r1_rooms import census
@@ -104,7 +94,6 @@
             verify_audit(cfg,cfg['r1_training']['room_audit'])
             result['augmented_room_audit']=cfg['r1_training']['room_audit']
             result['steps'].append('direction_twins')
-            check_host_scene(cfg, host, record=True)
         from student_pilot.r1_persisted import verify, scope, init_policy
         value=cfg['r1_training']
         closure=verify(value.get('handover_receipt'),value.get('p_run',{}),
@@ -153,6 +142,10 @@
             produced = bind_prepared(load(pinned(prepared['config'])),root/'b')
         cfg = load(pinned(produced));result['config']=produced
         result['steps'].append('r1_population.bind_prepared')
+        from student_pilot.r1_loader import production_audit
+        with scope(closure['paths']):
+            result['audit']=production_audit(cfg,root/'a')
+        result['steps'].append('r1_loader.production_audit')
         from student_pilot.r1_persisted import admission, scope
         with scope(closure['paths']):
             result['config'] = bind_handover(cfg,root/'h')
@@ -165,36 +158,25 @@
         if result['init_milestone'] not in (400,600) or result['absolute_resume_step'] != expected_start:
             raise ValueError('R1_PROOF_EXPORT_STEP_REQUIRED')
         result['steps'].append('persisted_handover')
-        # The receipt and audit must name the config published by the final bind.
-        from student_pilot.r1_loader import production_audit
-        with scope(closure['paths']):
-            result['audit']=production_audit(cfg,root/'a')
-        result['steps'].append('r1_loader.production_audit')
         if request.get('weights'):
             with scope(handover['paths']):
                 result['forward']=forward(cfg,root,result['absolute_resume_step'],device)
             result['steps'].append('all_rank_full_forward')
-        finish_host(cfg, root, host, result['audit'], named_refusals=True)
-        write(root/'host.json', host)
-        result['host_receipt'] = file_pin(root/'host.json')
         result['status']='ADMIT'
     except (ValueError,KeyError,TypeError,OSError,RuntimeError,ImportError) as error:
         result['refusal']=type(error).__name__+':'+str(error)
-    finally:
-        environment.close()
     write(root/'RESULT.json',result)
     return result
 
 
-def run(request, output, *, stage=None):
-    """Run host checks around staging; a kit may supply its authenticated copier."""
+def run(request, output):
     from student_pilot.r1_persisted import scope, proof_scope
     try:
         staging = verify_staging(request)
     except (ValueError,KeyError,TypeError,OSError):
-        return _run(request,output,stage=stage)
+        return _run(request,output)
     with proof_scope(), scope({p['sha256']:p['path'] for p in staging}):
-        return _run(request,output,stage=stage)
+        return _run(request,output)
 
 
 def main(argv=None):

```

run5: 4 launch lines removed; 3 rehearsal lines added. Functions: launch _run; rehearsal _run.

```diff

--- launch/tree/launch_r1/production_proof.py
+++ run5/tree/launch_r1/production_proof.py
@@ -91,9 +91,9 @@
         root, job_tmp, host = begin_host(cfg, root, request)
         environment.enter_context(host_environment(job_tmp))
         check_host_runtime(cfg, request, host)
-        cfg = stage_host(cfg, root, request, job_tmp, stage=stage, result=host)
-        check_host_scene(cfg, host, record=True)
-        check_host_selection(cfg, root, request, host, record=True)
+        cfg = stage_host(cfg, root, request, job_tmp, stage=stage)
+        check_host_scene(cfg, host)
+        check_host_selection(cfg, root, request, host)
         if cfg['r1_training'].get('direction_twins'):
             from student_pilot.r1_direction_twins import augment
             from student_pilot.r1_rooms import census
@@ -104,7 +104,6 @@
             verify_audit(cfg,cfg['r1_training']['room_audit'])
             result['augmented_room_audit']=cfg['r1_training']['room_audit']
             result['steps'].append('direction_twins')
-            check_host_scene(cfg, host, record=True)
         from student_pilot.r1_persisted import verify, scope, init_policy
         value=cfg['r1_training']
         closure=verify(value.get('handover_receipt'),value.get('p_run',{}),

```
