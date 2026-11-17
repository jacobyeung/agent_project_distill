# Package diff against production 0.tgz

Production SHA256: `446a432306b8e68ebfa32228071259a61ffd2ec0dada3ec43a664ba342ca540e`. The archive inventory contains 924 production files and 925 package files; 915 files match byte for byte. Nine existing files change and one is added.

`FILE_SHA256_DIFF.tsv` and `.json` list every member with both full hashes. `package.patch` contains every changed payload line; the readable diffs below include source line numbers and reasons. `PLAN_DIFF.json` expands the generated plan line into its exact changed fields.

All scorers, statistics, items, perturbations, call-cap code, reader/e2e code, tree, heads, authentication rows, and vendored runtime/environment/dependency inventories are byte-identical. Only h1eval/h10/launch.py changes within h1eval; only stage_restore.py changes within parity_kit. No reader source was repinned.

### `8.py`

Generated copy of orchard_h10/operator.py; same reason as that source.

```diff
--- production/8.py
+++ package/8.py
@@ -22,7 +22,7 @@
     mod=types.ModuleType('orchard_h10');mod.__path__=[];sys.modules['orchard_h10']=mod
     with tarfile.open(package/'0.tgz') as archive:
         cfg={**json.load(archive.extractfile('9.json')),**public}
-        for name in ('common','job'):
+        for name in ('common','export_pins','job'):
             path='orchard_h10/'+name+'.py';raw=archive.extractfile(path).read()
             if hashlib.sha256(raw).hexdigest()!=cfg['payload_pins'][path]['sha256']:raise ValueError('Helper differs')
             m=types.ModuleType('orchard_h10.'+name);m.__file__=path;sys.modules[m.__name__]=m
@@ -43,7 +43,7 @@
         raise ValueError('Stage the package under /project/community/jjyeung/'+cfg['token'])
     private=package/'a';private.mkdir(mode=0o700,exist_ok=True)
     if private.stat().st_mode & 0o077:raise ValueError('Private input directory must be 0700')
-    inputs=check_inputs(json.loads((private/'1.json').read_text()),cfg)
+    inputs=check_inputs(json.loads((private/'1.json').read_text()),cfg,package=package)
     opaque([str(package),str(package/'1.json'),str(package/'2.json')])
     for a in inputs['archives']:
         for part in a['parts']:
@@ -66,6 +66,8 @@
     if (cpu.get('plan')!=cfg['plan_sha256'] or cpu.get('inputs')!=digest(package/'a/1.json') or
             cpu.get('package')!=digest(package/'PACKAGE.json') or cpu.get('gpus')!=gpus or cpu.get('time')!=walltime):
         raise ValueError('Run the CPU check for these exact inputs, card count and time first')
+    from orchard_h10.job import check_inputs
+    check_inputs(json.loads((package/'a/1.json').read_text()),cfg,package=package)
     argv=submit_argv(cfg['token'],gpus,walltime)
     export=f"--export=A_N={gpus},A_T={seconds(walltime)},A_I={digest(package/'a/1.json')},A_C={digest(package/'2.json')}"
     argv[argv.index('--export=NONE')]=export

```

### `9.json`

Generated plan: new package token and hashes/sizes for the explicitly changed sources; the logical root and all other configuration remain fixed.

Both files contain one generated JSON line. Line 1 changes exactly these JSON fields; `package.patch` includes the complete literal line.

```json
[
  {
    "pointer": "/payload_pins/8.py/bytes",
    "production": 6776,
    "package": 6934
  },
  {
    "pointer": "/payload_pins/8.py/sha256",
    "production": "bf29f639b7090e60247d9ddc59c0c806a1b2910e2a6bdb289e52154cff1ddb9d",
    "package": "a65c37736e37ed294404e23ec40e41956651a8d45516560b9053f2efd0fff498"
  },
  {
    "pointer": "/payload_pins/b/parity_kit/stage_restore.py/bytes",
    "production": 10250,
    "package": 11260
  },
  {
    "pointer": "/payload_pins/b/parity_kit/stage_restore.py/sha256",
    "production": "df8923035ef9fb7a49c0c5b078a22e5e2718ccce46d9c86ee718961edd46fd5d",
    "package": "3eb2134f2d2368d50d3a55d107912dc1803819980058287c98515ce15bfcb429"
  },
  {
    "pointer": "/payload_pins/h1eval/h10/launch.py/bytes",
    "production": 19040,
    "package": 19347
  },
  {
    "pointer": "/payload_pins/h1eval/h10/launch.py/sha256",
    "production": "40bb4425b48d0d980129940ca7fe23b6718d3d02713c2f1302369bd479d69b94",
    "package": "d5959dd49d4963aabcd12650642b4553379500e521b81f5a7667d967a1f0cf40"
  },
  {
    "pointer": "/payload_pins/orchard_h10/build.py/bytes",
    "production": 10166,
    "package": 10247
  },
  {
    "pointer": "/payload_pins/orchard_h10/build.py/sha256",
    "production": "488730c9881049019dd4781a1373e591d0a61d5bb6a87650d98ce6a0a8d95464",
    "package": "a559e091b74127304d60fdb572ca3eedc1bfecffb3379d3c547b68ae658c828a"
  },
  {
    "pointer": "/payload_pins/orchard_h10/export_pins.py",
    "production": null,
    "package": {
      "bytes": 2719,
      "sha256": "e9aaa9d4b97a92423aa836e6f95e10e2adc9bc1a0cf49ff8439e833b86d3ab35"
    }
  },
  {
    "pointer": "/payload_pins/orchard_h10/job.py/bytes",
    "production": 14054,
    "package": 14114
  },
  {
    "pointer": "/payload_pins/orchard_h10/job.py/sha256",
    "production": "7595d0cd2852be3b8c27c2d987404ac9eaf3fe976d31ccda00827b5961f07815",
    "package": "63ffc26268b034c1f57c92bcf652d9f9e6212d1a755bc08c76e6d79a92253040"
  },
  {
    "pointer": "/payload_pins/orchard_h10/operator.py/bytes",
    "production": 6776,
    "package": 6934
  },
  {
    "pointer": "/payload_pins/orchard_h10/operator.py/sha256",
    "production": "bf29f639b7090e60247d9ddc59c0c806a1b2910e2a6bdb289e52154cff1ddb9d",
    "package": "a65c37736e37ed294404e23ec40e41956651a8d45516560b9053f2efd0fff498"
  },
  {
    "pointer": "/payload_pins/orchard_h10/prepare.py/bytes",
    "production": 3565,
    "package": 4421
  },
  {
    "pointer": "/payload_pins/orchard_h10/prepare.py/sha256",
    "production": "33c6b828c6cee95434020115abb959b532a648a02f464f96062eae0c24e6c57f",
    "package": "195cb79f7bca396ce5fca26b75e6a2ea18d7bec69003b5c40c9da0cf3b500607"
  },
  {
    "pointer": "/payload_pins/orchard_h10/runner.py/bytes",
    "production": 9655,
    "package": 9691
  },
  {
    "pointer": "/payload_pins/orchard_h10/runner.py/sha256",
    "production": "f533bfead435f210b778cc56697a14ef9944499e9159a519950cf96df5a6552e",
    "package": "dc37845fdb1133a3bfc2aa8b1b402507c863a972bebd748eb693949fb1443403"
  },
  {
    "pointer": "/template_pins/ORCHARD_ASSETS.json",
    "production": "7e1da1668b4bac1d101692486e45f45912ccdde13d9f8ba8ca72cdd2287bf809",
    "package": "a62285317a774cee040ceb5817e7ad7a7e08e12ea412b8f416cfb97b5a1c12ee"
  },
  {
    "pointer": "/token",
    "production": "b01ec87a6f29b",
    "package": "bf94a7976a7e9"
  }
]
```

### `b/parity_kit/stage_restore.py`

Select and authenticate preparation files from the pins, preserve their original binding paths, and retain every existing structural guard. The restore description names the selected export.

```diff
--- production/b/parity_kit/stage_restore.py
+++ package/b/parity_kit/stage_restore.py
@@ -68,7 +68,8 @@
 
 
 def stage(source, heads, meta, out, *, request=REQUEST, tree=TREE,
-          base_assets=BASE_ASSETS, model_manifest_tar=MODEL_MANIFEST_TAR):
+          base_assets=BASE_ASSETS, model_manifest_tar=MODEL_MANIFEST_TAR,
+          export_pins=None, data_root=None):
     source, heads, meta, out = map(lambda p: Path(p).resolve(), (source, heads, meta, out))
     if out.exists() and any(out.iterdir()):
         raise ValueError('restore output must be empty')
@@ -76,7 +77,21 @@
     cfg_path = meta / PREP / 'config.json'
     receipt_path = meta / PREP / 'prepared/s1_receipt.json'
     data_path = meta / 'fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json'
+    if export_pins is not None:
+        prep = export_pins['preparation']
+        cfg_path, receipt_path, data_path = [Path(data_root)/prep[n]['path']
+                                            for n in ('config', 'receipt', 'data_receipt')]
+        for name, path in zip(('config', 'receipt', 'data_receipt'),
+                              (cfg_path, receipt_path, data_path)):
+            checked(path, prep[name]['sha256'])
+            if path.stat().st_size != prep[name]['bytes']:
+                raise ValueError('Preparation size differs: ' + name)
+        req = dict(config=dict(path=prep['config']['source_path'], sha256=prep['config']['sha256']),
+                   data_receipt=prep['data_receipt'], artifact=export_pins['artifact'])
     cfg = read(checked(cfg_path, req['config']['sha256']))
+    if export_pins is not None and cfg.get('preparation') != dict(
+            path=prep['receipt']['source_path'], sha256=prep['receipt']['sha256']):
+        raise ValueError('Preparation receipt pin differs')
     receipt = read(checked(receipt_path, cfg['preparation']['sha256']))
     data = read(checked(data_path, req['data_receipt']['sha256']))
     artifact_path = checked(heads / 'artifact.json', req['artifact']['sha256'])
@@ -156,7 +171,7 @@
                                       step544_weights={e['name']: e['sha256'] for e in entries}),
                   deviations=[
                       dict(field='artifact.full_weights.path, artifact.heads.path', reason='Local files replace AWS paths; content pins stay unchanged.'),
-                      dict(field='receipt.model', reason='Base loads step-544 LM and ViT; load_export still checks and replaces every base tensor exactly.'),
+                      dict(field='receipt.model', reason='Base loads the pinned export LM and ViT; load_export still checks and replaces every base tensor exactly.'),
                       dict(field='receipt.depth_init', reason='Removed because strictly restored heads cover every private-depth tensor; see depth_overwrite.'),
                       dict(field='init_artifact', reason='Omitted during evaluation, as in read_runtime.load_model.'),
                       dict(field='admission', reason='Pinned mirrored metadata replaces AWS path and Git authentication. Training databases are not opened.'),

```

### `h1eval/h10/launch.py`

Read lineage and step from the job-local pin file and carry them unchanged into journal bindings; require the pin-file argument.

```diff
--- production/h1eval/h10/launch.py
+++ package/h1eval/h10/launch.py
@@ -174,6 +174,9 @@
     export=Path(args.export).resolve();artifact=Path(args.artifact_manifest).resolve()
     out=Path(args.out).resolve()
     if out==export or export in out.parents:raise ValueError('Output must be outside export')
+    identity=json.loads(Path(args.export_pin).read_text())
+    if (identity.get('lineage') not in ('SFT','RL') or type(identity.get('step')) is not int
+            or identity['step']<0):raise ValueError('Invalid export identity')
     binding=dict(schema='h10-shard-v1',item_set_sha256=manifest['item_set_sha256'],
                  items_sha256=sha(args.items),export_sha256=export_hash(export,getattr(args,'export_cache',None),getattr(args,'allocation',None)),
                  artifact_manifest_sha256=sha(artifact),reader_sha256=code_hash(Path(args.reader_root)/'e2e_reader'),
@@ -183,7 +186,7 @@
                  r0_code_sha256=sha(K/'tree/student_pilot/h1_r0.py'),
                  shard=args.shard,ids=[r['id'] for r in selected_items],
                  count=manifest['count'],arms=arms,modes=interventions,device=args.device,
-                 lineage='SFT',step=544,fixture=make_real is not None,
+                 lineage=identity['lineage'],step=identity['step'],fixture=make_real is not None,
                  r0_pin=manifest['r0_check']['pin'])
     if reviewed:
         binding.update(settings_sha256=digest(settings), mapping_sha256=mapping['sha256'],
@@ -312,6 +315,7 @@
 def parser():
     p=argparse.ArgumentParser(description=__doc__)
     for key in ('items','export','artifact-manifest','reader-root','out'):p.add_argument('--'+key,required=True)
+    p.add_argument('--export-pin',required=True)
     p.add_argument('--shard',default='0/1');p.add_argument('--types',default=None,help='comma list of question types to decode');p.add_argument('--arms',default='own,tower')
     p.add_argument('--modes',default=DEFAULT_MODES)
     p.add_argument('--tower-from',help='b04 run directory containing gpu_results/own_depth_p*/items.jsonl and LOAD_RECEIPT.json')

```

### `orchard_h10/build.py`

Keep the logical root independent of the new package token; describe the export reference in INPUTS.example.json and the local token inventory.

```diff
--- production/orchard_h10/build.py
+++ package/orchard_h10/build.py
@@ -123,7 +123,7 @@
         for n,raw in new.items():payload['b/'+n]=raw
     payload['8.py']=(K/'orchard_h10/operator.py').read_bytes()
     pins={n:dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)) for n,raw in payload.items()}
-    cfg=dict(schema='h10-orchard-v1',token=token,logical='/scratch/jjyeung/'+token,
+    cfg=dict(schema='h10-orchard-v1',token=token,logical='/scratch/jjyeung/b01ec87a6f29b',
              payload_pins=pins,
              template_pins={n:sha(T/n) for n in CORE},
              order=list(__import__('orchard_h10.common',fromlist=['ORDER']).ORDER),
@@ -161,6 +161,7 @@
     opaque([helper]);(destination/'3.py').write_text(helper)
     write(destination/'INPUTS.example.json',dict(schema=1,archives=[],files={},python=None,
         policy=dict(vnice=None,terminator=None),resume=None,
+        export_pin=dict(path='a/export.json',sha256=None,bytes=None),
         note='Fill and pin on Orchard; do not submit this unresolved example.'))
     (destination/'0.json').write_text(json.dumps(public,sort_keys=True)+'\n')
     write(destination/'PACKAGE.json',dict(token=token,files={n:sha(destination/n) for n in
@@ -173,7 +174,7 @@
             for n in sorted(old):report.write(f"- `{n}`: `{hashlib.sha256(old[n]).hexdigest()}` → `{pins['b/'+n]['sha256']}`.\n")
     mapping=K/'orchard_h10/TOKENS.json'
     old=json.loads(mapping.read_text()) if mapping.exists() else {}
-    old[token]=dict(package=str(destination.relative_to(K)),meaning='step-544 own dev-S1; registered modes; five ordered types')
+    old[token]=dict(package=str(destination.relative_to(K)),meaning='Pinned export; own dev-S1; registered modes and ordered types')
     write(mapping,old)
     return dict(directory=str(destination),token=token,code_bytes=len(raw),files=len(paths),plan=plan)
 

```

### `orchard_h10/export_pins.py`

Authenticate the pin file, validate its schema, and compare export paths, full hashes, and exact byte counts before staging.

```diff
--- production/orchard_h10/export_pins.py
+++ package/orchard_h10/export_pins.py
@@ -0,0 +1,70 @@
+"""Authenticate the operator's export identity before staging any archives."""
+import hashlib
+import json
+from pathlib import Path
+import re
+
+
+MEMBERS = dict(artifact='artifact.json', heads='heads.pt',
+               full_weights='full_weights/full_weights.json')
+PREPARATION = ('config', 'receipt', 'data_receipt')
+
+
+def relative(value):
+    p = Path(value)
+    if not value or p.is_absolute() or '..' in p.parts or str(p) != value or value == '.':
+        raise ValueError('Export path must be canonical and relative')
+    return p
+
+
+def pin(value):
+    if (not isinstance(value, dict) or not isinstance(value.get('sha256'), str)
+            or not re.fullmatch('[0-9a-f]{64}', value['sha256'])
+            or type(value.get('bytes')) is not int or value['bytes'] <= 0):
+        raise ValueError('Invalid export pin')
+
+
+def validate(value):
+    if value.get('schema') != 'h1-export-pins-v1':
+        raise ValueError('Export pin schema differs')
+    relative(value['member_directory'])
+    if (value.get('lineage') not in ('SFT', 'RL') or type(value.get('step')) is not int
+            or value['step'] < 0):
+        raise ValueError('Export requires SFT/RL and nonnegative integer step')
+    for name in MEMBERS:
+        pin(value[name])
+    if set(value['preparation']) != set(PREPARATION):
+        raise ValueError('Preparation keys differ')
+    paths = []
+    for name in PREPARATION:
+        item = value['preparation'][name]
+        pin(item); paths.append(relative(item['path']))
+        source = Path(item['source_path'])
+        if not source.is_absolute() or '..' in source.parts or str(source) != item['source_path']:
+            raise ValueError('Preparation source path differs')
+    if len(set(paths)) != len(paths):
+        raise ValueError('Preparation paths must be distinct')
+    return value
+
+
+def load(inputs, package):
+    spec = inputs['export_pin']
+    pin(spec)
+    if spec.get('path') != 'a/export.json':
+        raise ValueError('Require a/export.json')
+    path = Path(package)/spec['path']
+    raw = path.read_bytes()
+    if len(raw) != spec['bytes'] or hashlib.sha256(raw).hexdigest() != spec['sha256']:
+        raise ValueError('Export pin file differs')
+    return validate(json.loads(raw))
+
+
+def admit(inputs, cfg, export):
+    root = Path(cfg['logical'])/'d'/export['member_directory']
+    for name, member in MEMBERS.items():
+        declared = inputs['files'][name]
+        if (type(declared.get('bytes')) is not int
+                or any(declared[key] != export[name][key] for key in ('sha256', 'bytes'))):
+            raise ValueError('Export pin differs: '+name)
+        if declared['path'] != str(root/member):
+            raise ValueError('Export member path differs: '+name)

```

### `orchard_h10/job.py`

Use the fixed logical archive destination, replace only export constants with pin-file admission, authenticate the pin file before staging, and pass its contents to preparation and its job-local copy to workers.

```diff
--- production/orchard_h10/job.py
+++ package/orchard_h10/job.py
@@ -18,8 +18,10 @@
         raise ValueError('Plan digest differs')
 
 
-def check_inputs(inputs, cfg):
+def check_inputs(inputs, cfg, *, package=None):
     """Fail closed until every unresolved archive and dependency has a full pin."""
+    from orchard_h10.export_pins import load, admit
+    export = load(inputs, package or Path('/project/community/jjyeung')/cfg['token'])
     import re
     valid=lambda value:isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value)
     if 'types' in inputs:
@@ -37,7 +39,7 @@
             if not str(part.get('path','')).startswith('/project/community/jjyeung/'):
                 raise ValueError('Stage additional inputs to the registered community namespace')
         target=Path(a['destination'])
-        if target.is_absolute() or '..' in target.parts or str(target)!=f"sj/{cfg['token']}/d":
+        if target.is_absolute() or '..' in target.parts or str(target)!=str(Path('sj')/Path(cfg['logical']).relative_to('/scratch/jjyeung')/'d'):
             raise ValueError('Additional archives must unpack under the stable data root')
     needed={'artifact','heads','full_weights','g3t_weights','g3t_config','sam_checkpoint',
             'sam_receipt','selector_weights','selector_config','base_config','original_model'}
@@ -47,14 +49,12 @@
         path=Path(f.get('path',''))
         if not path.is_relative_to(Path(cfg['logical'])/'d') or '..' in path.parts:
             raise ValueError('Input file must live under the stable data root')
-    expected={'artifact':'1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef',
-              'heads':'8bb5e1510ee3a5a3959e82f2149c69903e98f46880b8a038bf4b951b8c21de91',
-              'full_weights':'211ae87b0bb03bb0c3d43c1c1412e0f346591ab4ddc75b4d754de2740da0a302',
-              'sam_checkpoint':'9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e',
+    admit(inputs, cfg, export)
+    expected={'sam_checkpoint':'9999e2341ceef5e136daa386eecb55cb414446a00ac2b55eb2dfd2f7c3cf8c9e',
               'selector_weights':'6d97c52407b7e106a7b475040558ba313589514c23c33b6994f4e7a0bb1df6c1'}
     for name,h in expected.items():
         if inputs['files'][name]['sha256']!=h:raise ValueError('Registered dependency differs: '+name)
-    for name,prefix in [('heads','8bb5e151'),('full_weights','211ae87b'),('g3t_weights','d460957b'),
+    for name,prefix in [('g3t_weights','d460957b'),
                         ('g3t_config','5aeb2acd'),('sam_checkpoint','9999e234')]:
         if not inputs['files'][name]['sha256'].startswith(prefix):raise ValueError('Registered pin prefix differs: '+name)
     for key in ('frames_root','sam_source'):
@@ -164,6 +164,8 @@
         cpu=json.loads((shared/'2.json').read_text())
         if cpu.get('plan')!=cfg['plan_sha256'] or cpu.get('inputs')!=os.environ['A_I'] or cpu.get('passed') is not True:
             raise ValueError('CPU receipt does not bind this submission')
+        from orchard_h10.export_pins import load
+        export_pins=load(inputs,shared)
         stage(root,cfg,inputs,S,J)
         write(root/'1.json',inputs)
         if time.time()>=end-cfg['stop_margin'] or (out/'metadata/STOP').exists():raise ValueError('No read budget after staging')
@@ -175,13 +177,13 @@
                    OPENBLAS_NUM_THREADS='16',CUDA_VISIBLE_DEVICES='')
         dispatch=root/'a';dispatch.mkdir(mode=0o700,exist_ok=True)
         (dispatch/'5.py').write_bytes((Path(__file__).parent/'entry.py').read_bytes())
-        write(dispatch/'0.json',dict(action=0,package=p,config=cfg,inputs=inputs))
+        write(dispatch/'0.json',dict(action=0,package=p,config=cfg,inputs={**inputs,'_export':export_pins}))
         opaque([f'{k}={v}' for k,v in env.items()])
         with (out/'logs/0.log').open('wb') as log:
             checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'0.json')],
                         env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
         restore_resume(inputs.get('resume'),out,cfg,S)
-        run_cfg=dict(export_cache=cfg['logical']+'/d/7.json',allocation=job,package=p,output=cfg['logical']+'/r',python=inputs['python'],
+        run_cfg=dict(export_pin=cfg['logical']+'/d/6.json',export_cache=cfg['logical']+'/d/7.json',allocation=job,package=p,output=cfg['logical']+'/r',python=inputs['python'],
                      export=cfg['logical']+'/d/e',binding=cfg['logical']+'/d/binding.json',
                      settings=cfg['logical']+'/d/settings.json',plan_sha256=cfg['plan_sha256'],
                      inputs_sha256=canonical({k:v for k,v in inputs.items() if k!='resume'}),

```

### `orchard_h10/operator.py`

Load the new pin module in the sealed standalone helper and authenticate a/export.json at check and submit.

```diff
--- production/orchard_h10/operator.py
+++ package/orchard_h10/operator.py
@@ -22,7 +22,7 @@
     mod=types.ModuleType('orchard_h10');mod.__path__=[];sys.modules['orchard_h10']=mod
     with tarfile.open(package/'0.tgz') as archive:
         cfg={**json.load(archive.extractfile('9.json')),**public}
-        for name in ('common','job'):
+        for name in ('common','export_pins','job'):
             path='orchard_h10/'+name+'.py';raw=archive.extractfile(path).read()
             if hashlib.sha256(raw).hexdigest()!=cfg['payload_pins'][path]['sha256']:raise ValueError('Helper differs')
             m=types.ModuleType('orchard_h10.'+name);m.__file__=path;sys.modules[m.__name__]=m
@@ -43,7 +43,7 @@
         raise ValueError('Stage the package under /project/community/jjyeung/'+cfg['token'])
     private=package/'a';private.mkdir(mode=0o700,exist_ok=True)
     if private.stat().st_mode & 0o077:raise ValueError('Private input directory must be 0700')
-    inputs=check_inputs(json.loads((private/'1.json').read_text()),cfg)
+    inputs=check_inputs(json.loads((private/'1.json').read_text()),cfg,package=package)
     opaque([str(package),str(package/'1.json'),str(package/'2.json')])
     for a in inputs['archives']:
         for part in a['parts']:
@@ -66,6 +66,8 @@
     if (cpu.get('plan')!=cfg['plan_sha256'] or cpu.get('inputs')!=digest(package/'a/1.json') or
             cpu.get('package')!=digest(package/'PACKAGE.json') or cpu.get('gpus')!=gpus or cpu.get('time')!=walltime):
         raise ValueError('Run the CPU check for these exact inputs, card count and time first')
+    from orchard_h10.job import check_inputs
+    check_inputs(json.loads((package/'a/1.json').read_text()),cfg,package=package)
     argv=submit_argv(cfg['token'],gpus,walltime)
     export=f"--export=A_N={gpus},A_T={seconds(walltime)},A_I={digest(package/'a/1.json')},A_C={digest(package/'2.json')}"
     argv[argv.index('--export=NONE')]=export

```

### `orchard_h10/prepare.py`

Stage authenticated preparation metadata, pass the selected files to restore, and use the selected config in reader settings. The sealed 544 fallback matches hashes and sizes exactly.

```diff
--- production/orchard_h10/prepare.py
+++ package/orchard_h10/prepare.py
@@ -20,11 +20,26 @@
     versions={m.__name__:m.__version__ for m in (torch,torchvision,transformers,scipy)}
     if receipt.get('versions')!=versions:raise ValueError('Environment versions differ from staged receipt')
     write(d/'ENVIRONMENT.json',dict(versions=versions,python=sys.executable))
+    pins=inputs['_export']
+    from orchard_h10.export_pins import validate
+    validate(pins)
+    # The sealed D0 metadata also supplies the unchanged 544 input archives.
+    bundled=dict(config=META/PREP/'config.json',receipt=META/PREP/'prepared/s1_receipt.json',
+                 data_receipt=META/'fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json')
+    for name,spec in pins['preparation'].items():
+        dest=d/spec['path']
+        if not dest.exists():
+            src=bundled[name]
+            if sha(src)!=spec['sha256'] or src.stat().st_size!=spec['bytes']:
+                raise ValueError('Stage the pinned preparation file: '+name)
+            dest.parent.mkdir(parents=True,exist_ok=True)
+            with dest.open('xb') as stream:stream.write(src.read_bytes())
+    write(d/'6.json',pins)
     # Each file was authenticated against INPUTS before entering the namespace.
     export=d/'e'; binding=d/'binding.json'
     stage(path('full_weights').parent,path('artifact').parent,META,export,
           request=REQUEST,tree=p/'tree',base_assets=path('base_config').parent,
-          model_manifest_tar=path('original_model'))
+          model_manifest_tar=path('original_model'),export_pins=pins,data_root=d)
     sam=dict(source_root=str(path('sam_receipt').parent/'source'),
              checkpoint_path=str(path('sam_checkpoint')),receipt_path=str(path('sam_receipt')))
     # The source tree has its own explicit logical path; never infer a host path.
@@ -37,7 +52,7 @@
     write(binding,dict(root=config['logical'],name='d/manifest.json',sha256=sha(d/'manifest.json'),
                        code_roots={k:str(v) for k,v in code.items()}))
     settings=dict(export_dir=str(export),artifact_manifest=str(binding),tree=str(p/'tree'),
-        config=str(META/PREP/'config.json'),frames_root=inputs['frames_root'],
+        config=str(d/pins['preparation']['config']['path']),frames_root=inputs['frames_root'],
         selector_head=str(path('selector_config').parent),sam3=sam,
         env_roots=inputs.get('env_roots',[]),arm='own_depth')
     if inputs.get('optional'):

```

### `orchard_h10/runner.py`

Pass the authenticated export pin copy to each worker.

```diff
--- production/orchard_h10/runner.py
+++ package/orchard_h10/runner.py
@@ -48,7 +48,7 @@
         if dest.exists():
             if dest.read_bytes()!=raw:raise ValueError('Item input changed')
         else:dest.write_bytes(raw)
-    args=['--items',str(dest),'--export',config['export'],'--artifact-manifest',config['binding'],
+    args=['--export-pin',config['export_pin'],'--items',str(dest),'--export',config['export'],'--artifact-manifest',config['binding'],
           '--reader-root',str(p/'b'),'--settings',config['settings'],
           '--out',str(Path(config['output'])/'metadata/journals'/str(t)/str(i)),
           '--arms','own','--shard',f"{i}/{cfg['cards']}",'--device',config.get('device','cuda:0'),

```

### Public package files

- `0.tgz`: changed. Sealed payload contains the changes above.
- `0.json`: changed. New token, payload digest/bytes, and plan digest.
  Changed line ranges: `@@ -1 +1 @@`.
- `CONFIG.json`: changed. New public token, payload digest/bytes, and plan digest.
  Changed line ranges: `@@ -1,6 +1,6 @@`.
- `BATCH.sh`: changed. Embedded numeric bootstrap descriptor and private-root token use the new package.
  Changed line ranges: `@@ -5,8 +5,8 @@`.
- `PACKAGE.json`: changed. New token and hashes of the generated package files.
  Changed line ranges: `@@ -1,10 +1,10 @@`.
- `INPUTS.example.json`: changed. Adds the required external export-pin reference.
  Changed line ranges: `@@ -1,5 +1,10 @@`.
- `3.py`: identical. Standalone loader remains byte-identical.
- `SUBMIT.cmd`: identical. Submission wrapper remains byte-identical.

`public.patch` contains every changed public text line, including the full encoded bootstrap line. The binary payload is covered by the complete member comparison above.

### Build and operator files outside the payload

`build_package.py` calls the production builder with local source locations; `audit_package.py` writes this audit. `fill_export.py` creates operator pins and the small preparation archive. `node_check.py` runs production staging/restore and invokes the supplied, byte-identical `submerge.py`. `export_544.json`, `export_TEMPLATE.json`, `inputs_544.json`, and `EXPORT_SCHEMA.md` define the input contract. `tests/test_package.py` tests the new package; `tests/test_constraints.py` retains the production audit and checks only the production extraction. The latter changes one line from its supplied version, removing src from the unchanged-extraction loop because src now contains the implementation. The complete new helper/test files are additions with no production counterpart. `REPORT.md` and `OPERATIONS_DELTA.md` describe this package. The original report is preserved verbatim as `REPORT_R1.md`.

### Supplied builder and stager comparison

`KIT_COMPARISON.json` inventories the supplied builder snapshot against production. `SOURCE_COMPARISON.md` retains the full supplied-source diffs: job.py, operator.py, and runner.py differ. The two supplied export stagers differ as modules, while parse_done and stage_export have identical function text. The production payload supplies every unchanged source in this build.
