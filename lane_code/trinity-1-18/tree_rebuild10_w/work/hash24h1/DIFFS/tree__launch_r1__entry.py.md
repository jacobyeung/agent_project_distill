# tree/launch_r1/entry.py

All diffs read launch C as old and the rehearsal as new. Missing files are explicit.

run4: 184 launch lines removed; 74 rehearsal lines added. Functions: launch <module>, begin_host, check_host_runtime, check_host_scene, check_host_selection, finish_host, frame_host, host_environment, localize, stage_host, verify_host_staging; rehearsal <module>, frame_host, localize.

```diff

--- launch/tree/launch_r1/entry.py
+++ run4/tree/launch_r1/entry.py
@@ -1,6 +1,5 @@
 """The CPU host proof gates R1's native preparation and trainer."""
 import os
-from contextlib import contextmanager
 from pathlib import Path
 import shutil
 import tempfile
@@ -106,9 +105,13 @@
     return start(cfg)
 
 
-def begin_host(cfg, root, request, *, job_tmp_token=None):
-    """Establish freshness and confinement before staging any job inputs."""
+def frame_host(cfg, root, request, *, job_tmp_token=None):
+    """Run the production CPU preparation from a fresh root; failures stay explicit."""
     from student_pilot.carrier_c1_run import identity
+    from student_pilot.checkpoint_space import plan
+    from student_pilot.carrier_c1_sweep import recipe_for
+    from student_pilot.r1_coverage import deferred
+    deferred(cfg, request)
     root = Path(root).resolve()
     job_tmp = fresh_tmp(root, request, job_tmp_token)
     if root.exists() and any(root.iterdir()):
@@ -123,12 +126,6 @@
                   missing=[], loader_audit={'complete':False})
     result['assertions']['empty_root'] = True
     result['assertions']['job_tmp'] = True
-    return root, job_tmp, result
-
-
-@contextmanager
-def host_environment(job_tmp):
-    """Confine caches and private directories, restoring the caller on refusal."""
     environment = ('TMPDIR', 'XDG_CACHE_HOME', 'HF_HOME', 'TRITON_CACHE_DIR', 'TORCH_HOME')
     saved = {name: os.environ.get(name) for name in environment}
     saved_tempdir = tempfile.tempdir
@@ -139,7 +136,74 @@
     os.chdir(job_tmp)
     previous_umask = os.umask(0o077)
     try:
-        yield
+        if os.environ.get('CUDA_VISIBLE_DEVICES', ''):
+            raise ValueError('CPU_ONLY_REQUIRED')
+        expected = plan(recipe_for(cfg), retained_archive_copies=1)
+        result['assertions']['disk_plan'] = cfg.get('checkpoint_disk_guard') == expected
+        if not result['assertions']['disk_plan']:
+            raise ValueError('R1_DISK_PLAN_DIFFERS')
+        binaries = {}
+        for name in request['binaries']:
+            binary = shutil.which(name)
+            if not binary:
+                raise ValueError('R1_BINARY_MISSING:'+name)
+            binaries[name] = file_pin(Path(binary).resolve())
+        result['binaries'] = binaries
+        result['assertions']['runtime_binaries'] = bool(binaries)
+        # The source staging closure must be supplied and checked before any import of native preparation.
+        if not request.get('staging') or not request.get('routing_selection'):
+            raise ValueError('R1_HOST_STAGING_AND_SELECTION_INPUTS_MISSING')
+        from launch_r2.staging import stage_inputs, validate_plan
+        staging = load(pinned(request['staging']))
+        temporary_paths(staging, job_tmp)
+        validate_plan(cfg, staging['entries'])
+        stage_inputs(staging['entries'], root)
+        def localize(value):
+            if isinstance(value, dict):
+                return {k:localize(v) for k,v in value.items()}
+            if isinstance(value, list):
+                return [localize(v) for v in value]
+            if isinstance(value, str) and value.startswith('u/'):
+                return str(root/value)
+            return value
+        staged_cfg = localize(cfg)
+        from student_pilot.r1_coverage import routing_request
+        minimal = routing_request(staged_cfg, localize(request))
+        if not request.get('routing_base') or not minimal and not request.get('routing_inputs'):
+            raise ValueError('R1_ROUTING_COMPOSITION_INPUTS_MISSING')
+        staged_cfg['streams']['routing'] = localize(request['routing_base'])
+        if not minimal:
+            staged_cfg['r1_training']['routing_inputs'] = localize(request['routing_inputs'])
+        temporary_paths(staged_cfg, job_tmp)
+        from student_pilot.scene_division_gate import check_bound
+        result['scene_division'] = check_bound(staged_cfg)
+        result['assertions']['scene_division'] = True
+        from student_pilot.s1_routing import build
+        from student_pilot.mdg_parent import model_pin
+        point = load(pinned(staged_cfg['streams']['pointing']))
+        regenerated = build(staged_cfg, root/'selection', point['division'], model_pin(staged_cfg))
+        selection = load(pinned(request['routing_selection']))
+        result['assertions']['routing_selection'] = digest(regenerated) == selection['regenerated_sha256']
+        if not result['assertions']['routing_selection']:
+            raise ValueError('R1_ROUTING_SELECTION_DIFFERS')
+        from student_pilot.s1_admission import admit as native_admit
+        write(root/'c.json', staged_cfg)
+        prepared = native_admit(file_pin(root/'c.json'), root/'p', [root], threads=8, prepare_only=True)
+        result['preparation'] = prepared
+        from student_pilot.r1_population import bind_prepared
+        produced = bind_prepared(load(pinned(prepared['config'])), root/'population')
+        result['population_config'] = produced
+        # This audit must come from the same production reader and final sampler indices.
+        from student_pilot.r1_loader import production_audit
+        result['loader_audit'] = production_audit(load(pinned(produced)), root/'audit')
+        result['config_identity'] = identity(load(pinned(produced)))
+        result['assertions']['directory_modes'] = all(p.stat().st_mode & 0o777 == 0o700
+            for p in [root, *[p for p in root.rglob('*') if p.is_dir()]])
+        if not all(result['assertions'].values()) or not result['loader_audit']['complete']:
+            raise ValueError('R1_HOST_ASSERTIONS_INCOMPLETE')
+        result['status'] = 'PASS'
+    except (ValueError, KeyError, TypeError, OSError) as error:
+        result['missing'].append(str(error))
     finally:
         os.umask(previous_umask)
         tempfile.tempdir = saved_tempdir
@@ -149,179 +213,5 @@
                 os.environ.pop(name, None)
             else:
                 os.environ[name] = value
-
-
-def check_host_runtime(cfg, request, result):
-    from student_pilot.checkpoint_space import plan
-    from student_pilot.carrier_c1_sweep import recipe_for
-    expected = plan(recipe_for(cfg), retained_archive_copies=1)
-    result['assertions']['disk_plan'] = cfg.get('checkpoint_disk_guard') == expected
-    if not result['assertions']['disk_plan']:
-        raise ValueError('R1_DISK_PLAN_DIFFERS')
-    binaries = {}
-    for name in request['binaries']:
-        binary = shutil.which(name)
-        if not binary:
-            raise ValueError('R1_BINARY_MISSING:'+name)
-        binaries[name] = file_pin(Path(binary).resolve())
-    result['binaries'] = binaries
-    result['assertions']['runtime_binaries'] = bool(binaries)
-
-
-def verify_host_staging(entries, root):
-    """Recheck native staging output with its hash and inventory checks."""
-    from launch_r2.staging import checked
-    root = Path(root).resolve()
-    archives = set()
-    for name, item in sorted(entries.items()):
-        try:
-            target = root/name
-            if not name.startswith('u/') or '..' in Path(name).parts or root not in target.resolve().parents:
-                raise ValueError('Staging target escaped the input root')
-            if 'archive' in item or 'directory' in item:
-                source = item.get('archive', item.get('directory'))
-                key = source.get('sha256') or source['inventory_sha256']
-                if not isinstance(key, str) or len(key) != 64 or any(c not in '0123456789abcdef' for c in key):
-                    raise ValueError('Invalid archive identity')
-                extracted = root/'x'/key
-                if key not in archives:
-                    if source.get('sha256'):
-                        checked(root/'a'/key, source['sha256'])
-                    elif not source.get('inventory'):
-                        raise ValueError('Archive has no authenticated inventory')
-                    for member, expected in source.get('inventory', {}).items():
-                        if Path(member).is_absolute() or '..' in Path(member).parts:
-                            raise ValueError('Staging inventory escaped its archive')
-                        checked(extracted/member, expected)
-                    archives.add(key)
-                member = Path(item.get('member', ''))
-                if member.is_absolute() or '..' in member.parts:
-                    raise ValueError('Staging member escaped its archive')
-                origin = extracted/member
-                if item.get('directory'):
-                    if not target.is_dir() or target.resolve() != origin.resolve():
-                        raise ValueError('Staging directory differs from its archive')
-                else:
-                    checked(origin, item['sha256'])
-                    checked(target, item['sha256'])
-            else:
-                checked(target, item['sha256'])
-        except (ValueError, KeyError, TypeError, OSError) as error:
-            raise ValueError('R1_HOST_STAGING_DIFFERS:'+name+':'+str(error)) from error
-
-
-def stage_host(cfg, root, request, job_tmp, *, stage=None, result=None):
-    """Stage authenticated inputs and retain the native routing composition."""
-    # The source staging closure must be supplied and checked before any import of native preparation.
-    if not request.get('staging') or not request.get('routing_selection'):
-        raise ValueError('R1_HOST_STAGING_AND_SELECTION_INPUTS_MISSING')
-    from launch_r2.staging import stage_inputs, validate_plan
-    staging = load(pinned(request['staging']))
-    temporary_paths(staging, job_tmp)
-    validate_plan(cfg, staging['entries'])
-    (stage_inputs if stage is None else stage)(staging['entries'], root)
-    if stage is None:
-        verify_host_staging(staging['entries'], root)
-    if result is not None:
-        result['stager'] = 'native' if stage is None else 'hook'
-        result['staging_plan_sha256'] = request['staging']['sha256']
-    def localize(value):
-        if isinstance(value, dict):
-            return {k:localize(v) for k,v in value.items()}
-        if isinstance(value, list):
-            return [localize(v) for v in value]
-        if isinstance(value, str) and value.startswith('u/'):
-            return str(root/value)
-        return value
-    staged_cfg = localize(cfg)
-    from student_pilot.r1_coverage import routing_request
-    minimal = routing_request(staged_cfg, localize(request))
-    if not request.get('routing_base') or not minimal and not request.get('routing_inputs'):
-        raise ValueError('R1_ROUTING_COMPOSITION_INPUTS_MISSING')
-    if result is not None:
-        original = staged_cfg['streams']['routing']
-        substituted = localize(request['routing_base'])
-        changes = dict(routing=dict(original=original, substituted=substituted,
-            original_sha256=original['sha256'], substituted_sha256=substituted['sha256']))
-        if not minimal:
-            original = staged_cfg['r1_training'].get('routing_inputs')
-            substituted = localize(request['routing_inputs'])
-            changes['routing_inputs'] = dict(original=original, substituted=substituted,
-                original_sha256=digest(original), substituted_sha256=digest(substituted))
-        result['routing_substitution'] = changes
-        result['routing_substituted'] = any(v['original'] != v['substituted'] for v in changes.values())
-    staged_cfg['streams']['routing'] = localize(request['routing_base'])
-    if not minimal:
-        staged_cfg['r1_training']['routing_inputs'] = localize(request['routing_inputs'])
-    temporary_paths(staged_cfg, job_tmp)
-    return staged_cfg
-
-
-def check_host_scene(cfg, result, *, record=False):
-    from student_pilot.scene_division_gate import check_bound
-    result['scene_division'] = check_bound(cfg)
-    if record:
-        result['scene_division_inputs'] = dict(division=cfg['scene_division'],
-            **{name:cfg['streams'][name] for name in ('vqa', 'routing')})
-    result['assertions']['scene_division'] = True
-
-
-def check_host_selection(cfg, root, request, result, *, record=False):
-    from student_pilot.s1_routing import build
-    from student_pilot.mdg_parent import model_pin
-    point = load(pinned(cfg['streams']['pointing']))
-    regenerated = build(cfg, root/'selection', point['division'], model_pin(cfg))
-    selection = load(pinned(request['routing_selection']))
-    result['assertions']['routing_selection'] = digest(regenerated) == selection['regenerated_sha256']
-    if record:
-        result['routing_selection'] = request['routing_selection']
-        result['regenerated_sha256'] = digest(regenerated)
-    if not result['assertions']['routing_selection']:
-        raise ValueError('R1_ROUTING_SELECTION_DIFFERS')
-
-
-def finish_host(cfg, root, result, loader_audit, *, named_refusals=False):
-    """Certify the configuration read by the final loader audit."""
-    from student_pilot.carrier_c1_run import identity
-    result['loader_audit'] = loader_audit
-    result['config_identity'] = identity(cfg)
-    result['assertions']['directory_modes'] = all(p.stat().st_mode & 0o777 == 0o700
-        for p in [root, *[p for p in root.rglob('*') if p.is_dir()]])
-    if named_refusals:
-        for name in ASSERTIONS:
-            if result['assertions'][name] is not True:
-                raise ValueError('R1_HOST_ASSERTION_FALSE:'+name)
-    if not all(result['assertions'].values()) or not result['loader_audit']['complete']:
-        raise ValueError('R1_HOST_ASSERTIONS_INCOMPLETE')
-    result['status'] = 'PASS'
-    return result
-
-
-def frame_host(cfg, root, request, *, job_tmp_token=None):
-    """Run the production CPU preparation from a fresh root; failures stay explicit."""
-    from student_pilot.r1_coverage import deferred
-    deferred(cfg, request)
-    root, job_tmp, result = begin_host(cfg, root, request, job_tmp_token=job_tmp_token)
-    with host_environment(job_tmp):
-        try:
-            if os.environ.get('CUDA_VISIBLE_DEVICES', ''):
-                raise ValueError('CPU_ONLY_REQUIRED')
-            check_host_runtime(cfg, request, result)
-            staged_cfg = stage_host(cfg, root, request, job_tmp)
-            check_host_scene(staged_cfg, result)
-            check_host_selection(staged_cfg, root, request, result)
-            from student_pilot.s1_admission import admit as native_admit
-            write(root/'c.json', staged_cfg)
-            prepared = native_admit(file_pin(root/'c.json'), root/'p', [root], threads=8, prepare_only=True)
-            result['preparation'] = prepared
-            from student_pilot.r1_population import bind_prepared
-            produced = bind_prepared(load(pinned(prepared['config'])), root/'population')
-            result['population_config'] = produced
-            # This audit must come from the same production reader and final sampler indices.
-            from student_pilot.r1_loader import production_audit
-            result['loader_audit'] = production_audit(load(pinned(produced)), root/'audit')
-            finish_host(load(pinned(produced)), root, result, result['loader_audit'])
-        except (ValueError, KeyError, TypeError, OSError) as error:
-            result['missing'].append(str(error))
     write(root/'receipt.json', result)
     return result

```

run5: 68 launch lines removed; 3 rehearsal lines added. Functions: launch <module>, check_host_scene, check_host_selection, stage_host, verify_host_staging; rehearsal check_host_scene, check_host_selection, localize, stage_host.

```diff

--- launch/tree/launch_r1/entry.py
+++ run5/tree/launch_r1/entry.py
@@ -168,49 +168,7 @@
     result['assertions']['runtime_binaries'] = bool(binaries)
 
 
-def verify_host_staging(entries, root):
-    """Recheck native staging output with its hash and inventory checks."""
-    from launch_r2.staging import checked
-    root = Path(root).resolve()
-    archives = set()
-    for name, item in sorted(entries.items()):
-        try:
-            target = root/name
-            if not name.startswith('u/') or '..' in Path(name).parts or root not in target.resolve().parents:
-                raise ValueError('Staging target escaped the input root')
-            if 'archive' in item or 'directory' in item:
-                source = item.get('archive', item.get('directory'))
-                key = source.get('sha256') or source['inventory_sha256']
-                if not isinstance(key, str) or len(key) != 64 or any(c not in '0123456789abcdef' for c in key):
-                    raise ValueError('Invalid archive identity')
-                extracted = root/'x'/key
-                if key not in archives:
-                    if source.get('sha256'):
-                        checked(root/'a'/key, source['sha256'])
-                    elif not source.get('inventory'):
-                        raise ValueError('Archive has no authenticated inventory')
-                    for member, expected in source.get('inventory', {}).items():
-                        if Path(member).is_absolute() or '..' in Path(member).parts:
-                            raise ValueError('Staging inventory escaped its archive')
-                        checked(extracted/member, expected)
-                    archives.add(key)
-                member = Path(item.get('member', ''))
-                if member.is_absolute() or '..' in member.parts:
-                    raise ValueError('Staging member escaped its archive')
-                origin = extracted/member
-                if item.get('directory'):
-                    if not target.is_dir() or target.resolve() != origin.resolve():
-                        raise ValueError('Staging directory differs from its archive')
-                else:
-                    checked(origin, item['sha256'])
-                    checked(target, item['sha256'])
-            else:
-                checked(target, item['sha256'])
-        except (ValueError, KeyError, TypeError, OSError) as error:
-            raise ValueError('R1_HOST_STAGING_DIFFERS:'+name+':'+str(error)) from error
-
-
-def stage_host(cfg, root, request, job_tmp, *, stage=None, result=None):
+def stage_host(cfg, root, request, job_tmp, *, stage=None):
     """Stage authenticated inputs and retain the native routing composition."""
     # The source staging closure must be supplied and checked before any import of native preparation.
     if not request.get('staging') or not request.get('routing_selection'):
@@ -220,11 +178,6 @@
     temporary_paths(staging, job_tmp)
     validate_plan(cfg, staging['entries'])
     (stage_inputs if stage is None else stage)(staging['entries'], root)
-    if stage is None:
-        verify_host_staging(staging['entries'], root)
-    if result is not None:
-        result['stager'] = 'native' if stage is None else 'hook'
-        result['staging_plan_sha256'] = request['staging']['sha256']
     def localize(value):
         if isinstance(value, dict):
             return {k:localize(v) for k,v in value.items()}
@@ -238,18 +191,6 @@
     minimal = routing_request(staged_cfg, localize(request))
     if not request.get('routing_base') or not minimal and not request.get('routing_inputs'):
         raise ValueError('R1_ROUTING_COMPOSITION_INPUTS_MISSING')
-    if result is not None:
-        original = staged_cfg['streams']['routing']
-        substituted = localize(request['routing_base'])
-        changes = dict(routing=dict(original=original, substituted=substituted,
-            original_sha256=original['sha256'], substituted_sha256=substituted['sha256']))
-        if not minimal:
-            original = staged_cfg['r1_training'].get('routing_inputs')
-            substituted = localize(request['routing_inputs'])
-            changes['routing_inputs'] = dict(original=original, substituted=substituted,
-                original_sha256=digest(original), substituted_sha256=digest(substituted))
-        result['routing_substitution'] = changes
-        result['routing_substituted'] = any(v['original'] != v['substituted'] for v in changes.values())
     staged_cfg['streams']['routing'] = localize(request['routing_base'])
     if not minimal:
         staged_cfg['r1_training']['routing_inputs'] = localize(request['routing_inputs'])
@@ -257,25 +198,19 @@
     return staged_cfg
 
 
-def check_host_scene(cfg, result, *, record=False):
+def check_host_scene(cfg, result):
     from student_pilot.scene_division_gate import check_bound
     result['scene_division'] = check_bound(cfg)
-    if record:
-        result['scene_division_inputs'] = dict(division=cfg['scene_division'],
-            **{name:cfg['streams'][name] for name in ('vqa', 'routing')})
     result['assertions']['scene_division'] = True
 
 
-def check_host_selection(cfg, root, request, result, *, record=False):
+def check_host_selection(cfg, root, request, result):
     from student_pilot.s1_routing import build
     from student_pilot.mdg_parent import model_pin
     point = load(pinned(cfg['streams']['pointing']))
     regenerated = build(cfg, root/'selection', point['division'], model_pin(cfg))
     selection = load(pinned(request['routing_selection']))
     result['assertions']['routing_selection'] = digest(regenerated) == selection['regenerated_sha256']
-    if record:
-        result['routing_selection'] = request['routing_selection']
-        result['regenerated_sha256'] = digest(regenerated)
     if not result['assertions']['routing_selection']:
         raise ValueError('R1_ROUTING_SELECTION_DIFFERS')
 

```
