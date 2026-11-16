The derivation tool retains D0’s data-only rules and adds one separately validated code-tree override. No arbitrary `b/`, job-script, code-pin, optimizer, or recipe override is accepted.

The exact patch is [evidence/derive.patch](evidence/derive.patch). Every changed line appears below with its purpose. Blank lines only separate the corresponding blocks.

| Location | Change | Line | Reason |
|---|---|---|---|
| D0 1 | − | `"""Derive a data-only kit from sealed kit 07ca49df's own records: same trainer tree, b/ gate, job scripts and 7.json;` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 1 | + | `"""Derive a data-only kit (or a narrowly admitted code-tree kit) from sealed kit 07ca49df's own records: same trainer tree, b/ gate, job scripts and 7.json;` | Document and expose only the declared code-tree and config override fields. |
| D0 9 | − | `  config: {streams: {vqa?, routing?}, init_artifact?, s1_routing: {selection?, catalog?}?}` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 9 | + | `  code_tree: {archive: {path, sha256}, pin: {path, sha256}, archive_record?: {path, sha256}}` | Document and expose only the declared code-tree and config override fields. |
| H1 10 | + | `           validates deterministic source archive, regenerates tree bindings, installs fixed stop bridge;` | Document and expose only the declared code-tree and config override fields. |
| H1 11 | + | `           archive_record is required for READY and must attest this archive off scratch.` | Document and expose only the declared code-tree and config override fields. |
| H1 12 | + | `  config: {h1?, milestones?, recipe: {milestones?, scheduled_sampling?}?, scheduled_sampling?, streams: {vqa?, routing?}, init_artifact?, s1_routing: {selection?, catalog?}?}` | Document and expose only the declared code-tree and config override fields. |
| D0 35 | − | `import copy, hashlib, json, re, shutil, sys` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 38 | + | `import copy, hashlib, json, re, shutil, sys, tarfile` | Document and expose only the declared code-tree and config override fields. |
| D0 51 | − | `       'export_member_names', 'e00_listing'}` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 54 | + | `       'export_member_names', 'e00_listing', 'code_tree'}` | Document and expose only the declared code-tree and config override fields. |
| D0 53 | − | `CONFIG = {'streams', 'init_artifact', 's1_routing'}` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 56 | + | `CONFIG = {'streams', 'init_artifact', 's1_routing', 'h1', 'milestones', 'recipe', 'scheduled_sampling'}` | Document and expose only the declared code-tree and config override fields. |
| H1 224 | + | `    if 'code_tree' in over:` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 225 | + | `        regen &#124;= code_records(json.loads((out / 'k/7.json').read_text()))` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 359 | + | `` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 360 | + | `# Code changes have a separate validator; data staging never gains executable destinations.` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 361 | + | `H1 = dict(faithful_own_camera_rows=True, routing_pose_targets=True,` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 362 | + | `          camera_types=['camera_displacement', 'camera_movement_direction', 'camera_rotation'],` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 363 | + | `          stop_after_step=200, metrics=True,` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 364 | + | `          r0_rooms=dict(path='auth/R0_ROOMS.txt', sha256='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'))` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 365 | + | `SAMPLING = dict(force_from_step=1, max_own_probability=0.5)` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 366 | + | `` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 367 | + | `def validate_h1(over):` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 368 | + | `    oc = over.get('config', {})` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 369 | + | `    new = set(oc) & {'h1', 'milestones', 'recipe', 'scheduled_sampling'}` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 370 | + | `    if new and 'code_tree' not in over: refuse('new training settings require code_tree')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 371 | + | `    if 'h1' in oc and enc(oc['h1']) != enc(H1): refuse('only the registered h1 block is admitted')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 372 | + | `    if 'milestones' in oc and enc(oc['milestones']) != enc([100, 200]): refuse('only milestones [100, 200] admitted')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 373 | + | `    for value in [oc.get('scheduled_sampling', {}), oc.get('recipe', {}).get('scheduled_sampling', {})]:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 374 | + | `        if not isinstance(value, dict) or set(value)-set(SAMPLING) or any(enc(value[k]) != enc(SAMPLING[k]) for k in value):` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 375 | + | `            refuse('scheduled_sampling permits only force_from_step=1 and max_own_probability=0.5')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 376 | + | `    if set(oc.get('recipe', {}))-{'milestones', 'scheduled_sampling'}: refuse('unknown recipe keys')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 377 | + | `    if 'milestones' in oc.get('recipe', {}) and oc['recipe']['milestones'] != [100, 200]: refuse('recipe milestones differ')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 378 | + | `    if 'code_tree' in over:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 379 | + | `        if new != {'h1', 'milestones', 'recipe', 'scheduled_sampling'} or oc['recipe'] != dict(milestones=[100, 200], scheduled_sampling=SAMPLING) or oc['scheduled_sampling'] != SAMPLING:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 380 | + | `            refuse('code_tree requires the complete registered settings')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 381 | + | `` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 382 | + | `def code_records(code):` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 383 | + | `    return {'k/7.json', 'k/s1_record.json', 'k/archive.json', 'k/' + Path(code['archive']['path']).name,` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 384 | + | `            'b/r.sh', 'b/h.py', 'b/i.py', 'job.sh'}` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 385 | + | `` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 386 | + | `def read_override_pin(value):` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 387 | + | `    if not isinstance(value, dict) or set(value) != {'path', 'sha256'} or not HEX64.fullmatch(str(value['sha256'])):` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 388 | + | `        refuse('malformed code override pin')` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 389 | + | `    if sha(value['path']) != value['sha256']: refuse('code override pin differs')` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 390 | + | `    return Path(value['path'])` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 391 | + | `` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 392 | + | `def replace_once(path, before, after):` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 393 | + | `    text = path.read_text()` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 394 | + | `    if text.count(before) != 1: refuse('fixed runtime patch does not match ' + path.name)` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 395 | + | `    path.write_text(text.replace(before, after))` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 396 | + | `` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 397 | + | `def install_code(kit, out, over, cfg, cur, launch):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 398 | + | `    value = over['code_tree']` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 399 | + | `    if not isinstance(value, dict) or set(value)-{'archive', 'pin', 'archive_record'} or not {'archive', 'pin'} <= set(value):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 400 | + | `        refuse('unknown or incomplete code_tree keys')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 401 | + | `    archive = read_override_pin(value['archive']); pin = read_override_pin(value['pin'])` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 402 | + | `    code = json.loads(pin.read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 403 | + | `    if set(code) != {'schema', 'commit', 'tree_sha256', 'files', 'sources', 'operation_sources', 'archive'} or code['schema'] != 'c1-sealed-source-v1':` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 404 | + | `        refuse('code pin schema differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 405 | + | `    tree = digest(code['files']); name = 't_' + tree[:16] + '.tar'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 406 | + | `    if code['tree_sha256'] != tree or code['commit'] != 'sha256:' + tree or code['archive'] != dict(path=KIT_LOGICAL + name, sha256=sha(archive)):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 407 | + | `        refuse('code tree/archive identity differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 408 | + | `    members = {}; order = []` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 409 | + | `    with tarfile.open(archive) as tf:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 410 | + | `        for m in tf:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 411 | + | `            if not m.isfile() or not safe_rel(m.name) or m.name in members or m.size > 16_000_000 or (m.uid,m.gid,m.uname,m.gname,m.mtime) != (0,0,'','',0) or m.mode not in (0o644,0o755):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 412 | + | `                refuse('unsafe or nondeterministic source member')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 413 | + | `            order.append(m.name); members[m.name] = hashlib.sha256(tf.extractfile(m).read()).hexdigest()` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 414 | + | `    if order != sorted(order) or members != code['files']: refuse('archive members differ from code pin')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 415 | + | `    for key in ('sources', 'operation_sources'):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 416 | + | `        if not code[key] or any(members.get(n) != h for n,h in code[key].items()): refuse('source closure differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 417 | + | `    if members.get('auth/R0_ROOMS.txt') != H1['r0_rooms']['sha256']: refuse('R0 rooms not sealed in tree')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 418 | + | `    shutil.copyfile(archive, out / 'k' / name); shutil.copyfile(pin, out / 'k/7.json')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 419 | + | `    record = json.loads((kit / 'k/s1_record.json').read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 420 | + | `    record['trees']['trainer'] = dict(commit=code['commit'], file_count=len(members), files=members)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 421 | + | `    write(out / 'k/s1_record.json', record)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 422 | + | `    cur['record'] = dict(file=KIT_LOGICAL + 's1_record.json', sha256=sha(out / 'k/s1_record.json'))` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 423 | + | `    cur['trainer'] = dict(file=code['archive']['path'], sha256=code['archive']['sha256'])` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 424 | + | `    cur['commit'] = code['commit']; cfg['code'] = dict(path=KIT_LOGICAL + '7.json', sha256=sha(out / 'k/7.json'))` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 425 | + | `    launch['source_revision'] = code['commit']; launch['slot']['wall_seconds'] = 46800` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 426 | + | `    if 'archive_record' in value:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 427 | + | `        rec = json.loads(read_override_pin(value['archive_record']).read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 428 | + | `        location = str(archive)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 429 | + | `        if not PART.fullmatch(location): refuse('archive attestation must name the uploaded project archive')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 430 | + | `        if rec.get('status') != 'ARCHIVED' or rec.get('durable') is not True or rec.get('location') != location or rec.get('sha256') != sha(archive) or rec.get('tree_sha256') != tree or rec.get('bytes') != archive.stat().st_size:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 431 | + | `            refuse('archive attestation differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 432 | + | `    else:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 433 | + | `        if over.get('status') == 'READY': refuse('READY needs an off-scratch archive attestation')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 434 | + | `        rec = dict(schema='s1-source-archive-v1', status='PENDING', durable=False,` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 435 | + | `                   sha256=sha(archive), tree_sha256=tree, bytes=archive.stat().st_size)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 436 | + | `    write(out / 'k/archive.json', rec)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 437 | + | `    if '4.json' in over.get('add_k', {}):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 438 | + | `        auth = json.loads((out / 'k/4.json').read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 439 | + | `        if auth.get('source_revision') != code['commit'] or auth.get('config_sha256') != identity(cfg) or auth.get('production_go_granted') is not False or auth.get('wall_seconds') != 46800:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 440 | + | `            refuse('new source needs its own conditional authorization')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 441 | + | `    # Both paths refer to the same inode through c.sh's NR -> X/runs writable bind.` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 442 | + | `    replace_once(out / 'b/r.sh', '    printf \'USR1\\n\' >> "$stop_file"',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 443 | + | `        '    printf \'USR1\\n\' >> "$stop_file"\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 444 | + | `        '    run_dir=$(/usr/bin/python3 -I -c \'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])\' "$HX/k/launch.json")\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 445 | + | `        '    mkdir -p "$run_dir"\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 446 | + | `        '    printf \'USR1\\n\' >> "$run_dir/stop.${SLURM_JOB_ID:-local}.request"')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 447 | + | `    replace_once(out / 'b/h.py', 'except (FileNotFoundError, ProcessLookupError):',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 448 | + | `                 'except (FileNotFoundError, ProcessLookupError, PermissionError):')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 449 | + | `    replace_once(out / 'b/i.py', '        except FileNotFoundError: pass',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 450 | + | `                 '        except (FileNotFoundError, PermissionError): pass')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 451 | + | `    replace_once(out / 'job.sh', '#SBATCH --time=24:00:00', '#SBATCH --time=13:00:00')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 452 | + | `` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| D0 357 | − | `    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the data-only set ' + str(sorted(set(over['config']) - CONFIG)))` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 456 | + | `    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the admitted set ' + str(sorted(set(over['config']) - CONFIG)))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 463 | + | `    validate_h1(over)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 385 | − | `    changing = bool(over.get('config') or over.get('deployment') or over.get('add_k')` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 485 | + | `    changing = bool(over.get('code_tree') or over.get('config') or over.get('deployment') or over.get('add_k')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 510 | + | `    for name in ('h1', 'milestones'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 511 | + | `        if name in oc: cfg[name] = copy.deepcopy(oc[name])` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 512 | + | `    for name in ('scheduled_sampling', 'recipe'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 513 | + | `        if name in oc:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 514 | + | `            cfg[name] = copy.deepcopy(cfg[name])` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 515 | + | `            for k, v in oc[name].items():` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 516 | + | `                if name == 'recipe' and k == 'scheduled_sampling':` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 517 | + | `                    cfg[name][k] = {**cfg[name][k], **v}` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 518 | + | `                else: cfg[name][k] = copy.deepcopy(v)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 533 | + | `` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 534 | + | `    if 'code_tree' in over:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 535 | + | `        install_code(kit, out, over, cfg, cur, launch)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 448 | − | `    code = json.loads((kit / 'k/7.json').read_text())` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 560 | + | `    code = json.loads((out / 'k/7.json').read_text())` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |

**Trainer and shipped-runtime changes**

`student_pilot/carrier_c1_run.py`: Poll the job-specific stop request at startup and after each optimizer update. The existing all-reduce, checkpoint, milestone export and stop path remain intact.

```diff
--- supplied/student_pilot/carrier_c1_run.py
+++ shipped/student_pilot/carrier_c1_run.py
@@ -2316,7 +2316,7 @@
             dist.broadcast_object_list(state,src=0)
         gates.ema=dict(state[0])
     last_save=time.monotonic()
-    request=torch.tensor([int(stop[0] or steps==start_step)],device=device)
+    request=torch.tensor([int(stop[0] or (output/('stop.'+os.environ.get('SLURM_JOB_ID','local')+'.request')).exists() or steps==start_step)],device=device)
     if distributed:
         # Startup durations can differ. All ranks must use the shortest budget.
         end=torch.tensor([steps],device=device)
@@ -2388,7 +2388,7 @@
         pending += timing.get('export_seconds',0.) if step in recipe['milestones'] else 0.
         next_cost = max(info['wall_seconds'],timing.get('p95_step_seconds',0.)) + timing.get('checkpoint_seconds',0.)
         next_cost += timing.get('export_seconds',0.) if (step+1 in recipe['milestones'] or recipe.get('export_at_stop')) else 0.
-        request=torch.tensor([int(stop[0] or time.monotonic()-started+pending+next_cost >=
+        request=torch.tensor([int(stop[0] or (output/('stop.'+os.environ.get('SLURM_JOB_ID','local')+'.request')).exists() or time.monotonic()-started+pending+next_cost >=
             recipe['wall_seconds']-recipe['stop_before_seconds'])],device=device)
         if distributed:
             dist.all_reduce(request,op=dist.ReduceOp.MAX)
```

`student_pilot/h1_r0.py`: Resolve the pinned room file inside the flat trainer archive. Its bytes remain bdb5d402…; no room membership changes.

```diff
--- supplied/student_pilot/h1_r0.py
+++ shipped/student_pilot/h1_r0.py
@@ -49,7 +49,7 @@
             raise ValueError('R0 pin differs from the registered R0_SHA256')
         resolved = dict(pin)
         if not Path(pin['path']).is_absolute():
-            root = Path(__file__).resolve().parents[2]
+            root = Path(__file__).resolve().parents[1]
             candidate = (root/pin['path']).resolve()
             if not candidate.is_relative_to(root):raise ValueError('R0 pin escapes kit root')
             resolved['path'] = str(candidate)
```

`b/r.sh`: Write the request into the run directory that c.sh binds into every rank’s namespace. Job-specific names prevent stale requests from stopping a resumed allocation.

```diff
--- supplied/b/r.sh
+++ shipped/b/r.sh
@@ -12,6 +12,9 @@
 stop_file="$HX/o/${SLURM_JOB_ID:-local}.stop"
 on_stop() {
     printf 'USR1\n' >> "$stop_file"
+    run_dir=$(/usr/bin/python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])' "$HX/k/launch.json")
+    mkdir -p "$run_dir"
+    printf 'USR1\n' >> "$run_dir/stop.${SLURM_JOB_ID:-local}.request"
     if [[ -n "$admission_child" ]]; then
         kill -USR1 "$admission_child" 2>/dev/null || true
     elif [[ -n "$child" && -n "$X" ]]; then
```

`b/h.py`: Continue walking when a process namespace denies /proc access.

```diff
--- supplied/b/h.py
+++ shipped/b/h.py
@@ -15,7 +15,7 @@
             if (encoded in command and command.index(encoded)+1 < len(command)
                     and command[command.index(encoded)+1] == str(root).encode()):
                 os.kill(pid, signal.SIGUSR1)
-        except (FileNotFoundError, ProcessLookupError):
+        except (FileNotFoundError, ProcessLookupError, PermissionError):
             pass
 
 
```

`b/i.py`: Do not unwind the supervisor when /proc/<pid>/environ is denied. The run-file stop bridge remains available.

```diff
--- supplied/b/i.py
+++ shipped/b/i.py
@@ -115,7 +115,7 @@
             env=Path(f'/proc/{child}/environ').read_bytes().split(b'\0')
             if any(v.startswith(b'LOCAL_RANK=') for v in env): os.kill(child,signal.SIGUSR1)
         except ProcessLookupError: pass
-        except FileNotFoundError: pass
+        except (FileNotFoundError, PermissionError): pass
 
 def launcher(root,mode,arm,cfg):
     command=[sys.executable,'-B']
```

`job.sh`: Declare the 13-hour allocation; retain the recipe’s sealed 24-hour horizon and stop reserve.

```diff
--- supplied/job.sh
+++ shipped/job.sh
@@ -4,7 +4,7 @@
 #SBATCH --gpus-per-node=4
 #SBATCH --cpus-per-task=48
 #SBATCH --mem=800G
-#SBATCH --time=24:00:00
+#SBATCH --time=13:00:00
 #SBATCH --no-requeue
 #SBATCH --signal=B:USR1@3600
 set -euo pipefail
```

`jb.sh`: Use only the new run, kit, persistent root and verifier; set the allocation and fallback deadline to 13 hours. Retain R11’s slot publication checks.

```diff
--- supplied/jb.sh
+++ shipped/jb.sh
@@ -1,19 +1,12 @@
 #!/bin/bash
-# Job B: wrapper around the derived kit's own job.sh (kit f5c353f7, a data-only derivation of sealed kit 07ca49df; run 359fcc3c,
-# persistent root /project/community/jjyeung/okh7/r/63e57182) on Orchard `advanced`. Same steps as the 169097 wrapper, plus two checks first.
-# Before job.sh: restore the newest verified state slot into RUN on a node without a complete checkpoint.
-# During: relay Slurm's USR1 (3,600 s before the limit) to job.sh (which execs the kit's r.sh, whose trap stops safely);
-# mirror RUN/binding.json to the persistent root once the in-job admission writes it (first leg).
-# After: archive the newest complete checkpoint with RUN/inputs and RUN/binding.json into .part files of the other slot,
-# check every command's status, re-read once against the checkpoint's complete.json, then rename and record the content check. The kit's r8.py writes RUN.json (exclusive)
-# and refuses a cold start when an earlier leg or slot exists. /tmp does not survive between jobs.
-#SBATCH -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 24:00:00
+# Conditional four-rank entry; a separate submission approval is required.
+#SBATCH -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 13:00:00
 #SBATCH --no-requeue --signal=B:USR1@3600
 set -uo pipefail
 export PATH=/usr/local/bin:/usr/bin:/bin
 export TK_JOB_START="$(date +%s)"   # one wall clock for restore, staging, admission and training (job.sh must keep it)
-KH=/project/community/jjyeung/okh7/x_f5c353f7 RUN=/tmp/jjyeung/okit_8865619b/runs/359fcc3c
-RS=/project/community/jjyeung/okh7/r/63e57182 LOG=$KH/o/${SLURM_JOB_ID}.w.steps
+KH=/project/community/jjyeung/okh7/x_4b3114cf RUN=/tmp/jjyeung/okit_8865619b/runs/17c4ffa4
+RS=/project/community/jjyeung/okh7/r/766136c1 LOG=$KH/o/${SLURM_JOB_ID}.w.steps
 step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
 newest() {  # newest verified slot: prints "slot step" (empty if none)
     for s in A B; do [[ -f $RS/$s.json ]] && /usr/bin/python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["slot"], d["step"]) if d.get("verified") is True else None' "$RS/$s.json"; done | sort -k2,2n | tail -1
@@ -35,7 +28,7 @@
     || { step "refused: export sessions incomplete for run ${RUN##*/}"; exit 5; }
 step "export sessions present for run ${RUN##*/}"
 # Actual archive contents of every new staging entry, before c.sh extracts them (vt.py; sealed k/0.json pinned inside).
-/usr/bin/python3 -I /project/community/jjyeung/okh7/i_bb09a77d/vt.py "$KH" /project/community/jjyeung/okh7/x_07ca49df/k/0.json > "$KH/o/${SLURM_JOB_ID}.vt.json" 2>&1 \
+/usr/bin/python3 -I /project/community/jjyeung/okh7/i_1be16f28/v.py "$KH" /project/community/jjyeung/okh7/x_07ca49df/k/0.json > "$KH/o/${SLURM_JOB_ID}.vt.json" 2>&1 \
     || { step "refused: staging entry check: $(tail -c 300 "$KH/o/${SLURM_JOB_ID}.vt.json")"; exit 5; }
 step "staging entries verified"
 read -r slot sstep < <(newest || true)
@@ -102,7 +95,7 @@
     # as the step-544 repack used it), check size and md5 against the stream, record it, exit 6. SLOT_SKIPPED otherwise.
     step "slot copy to project impossible: checkpoint $cstep needs $need B, $RS has $avail B free; streaming the slot to GCS"
     ckn=$(basename "$ck"); obj="q8/d2d30e36/${RUN##*/}_s${cstep}.tar"; gs="gs://cmu-gpucloud-jjyeung/$obj"; sum="$RUN/.gslot.$SLURM_JOB_ID.json"
-    left=$(( TK_JOB_START + 86400 - $(date +%s) - 300 )); t0=$(date +%s); gok=0
+    left=$(( TK_JOB_START + 46800 - $(date +%s) - 300 )); t0=$(date +%s); gok=0
     if (( left > 600 )); then
         tar --hard-dereference -cf - -C "$RUN" "$ckn" inputs binding.json \
             | /usr/bin/python3 -I -c '
```

The trainer also adds the exact supplied `auth/R0_ROOMS.txt` inside its archive. All supplied H1 tree changes relative to D0 are enumerated with before/after hashes in [evidence/tree_changes.json](evidence/tree_changes.json).

`payload/f.py` preserves the faithful gate computation, uses the opaque deployed tree directory, records the input receipt hash, and classifies unreadable/invalid SQLite inputs as exit 2. The new read-only staging verifier checks actual tar members and whole-archive digests, including trailing bytes.

Tests: `evidence/derivation.json`, `evidence/archive_layout.json`, `evidence/stop_bridge/result.json`, `evidence/gate_binding.json`, `evidence/staging_test/result.json`, and `evidence/cpu/fallback_final/result.json`. The four-rank torchrun chain is blocked by denied sockets; its failure log is retained. The step-200 fallback uses a native tiny model and real checkpoint/export serialization with local one-rank collective stand-ins.
