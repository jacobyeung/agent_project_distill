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
| H1 371 | + | `    if 'h1' in oc and enc(oc['h1']) != enc(H1): refuse('only the registered settings are admitted')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 372 | + | `    if 'milestones' in oc and enc(oc['milestones']) != enc([100, 200]): refuse('only milestones [100, 200] admitted')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 373 | + | `    for value in [oc.get('scheduled_sampling', {}), oc.get('recipe', {}).get('scheduled_sampling', {})]:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 374 | + | `        if not isinstance(value, dict) or set(value)-set(SAMPLING) or any(enc(value[k]) != enc(SAMPLING[k]) for k in value):` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 375 | + | `            refuse('scheduled_sampling permits only force_from_step=1 and max_own_probability=0.5')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 376 | + | `    if set(oc.get('recipe', {}))-{'milestones', 'scheduled_sampling'}: refuse('unknown recipe keys')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 377 | + | `    if 'milestones' in oc.get('recipe', {}) and oc['recipe']['milestones'] != [100, 200]: refuse('recipe milestones differ')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 378 | + | `    if 'code_tree' in over:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 379 | + | `        if '4.json' not in over.get('add_k', {}): refuse('code_tree requires add_k 4.json')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 380 | + | `        if new != {'h1', 'milestones', 'recipe', 'scheduled_sampling'} or oc['recipe'] != dict(milestones=[100, 200], scheduled_sampling=SAMPLING) or oc['scheduled_sampling'] != SAMPLING:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 381 | + | `            refuse('code_tree requires the complete registered settings')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 382 | + | `` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 383 | + | `def code_records(code):` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 384 | + | `    return {'k/7.json', 'k/s1_record.json', 'k/archive.json', 'k/' + Path(code['archive']['path']).name,` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 385 | + | `            'b/c.sh', 'b/p0.sh', 'b/r.sh', 'b/h.py', 'b/i.py', 'job.sh'}` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 386 | + | `` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 387 | + | `def read_override_pin(value):` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 388 | + | `    if not isinstance(value, dict) or set(value) != {'path', 'sha256'} or not HEX64.fullmatch(str(value['sha256'])):` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 389 | + | `        refuse('malformed code override pin')` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 390 | + | `    if sha(value['path']) != value['sha256']: refuse('code override pin differs')` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 391 | + | `    return Path(value['path'])` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 392 | + | `` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 393 | + | `def replace_once(path, before, after):` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 394 | + | `    text = path.read_text()` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 395 | + | `    if text.count(before) != 1: refuse('fixed runtime patch does not match ' + path.name)` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 396 | + | `    path.write_text(text.replace(before, after))` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 397 | + | `` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 398 | + | `def install_code(kit, out, over, cfg, cur, launch):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 399 | + | `    if over['run_key'] != '17c4ffa4': refuse('unregistered run')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 400 | + | `    value = over['code_tree']` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 401 | + | `    if not isinstance(value, dict) or set(value)-{'archive', 'pin', 'archive_record'} or not {'archive', 'pin'} <= set(value):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 402 | + | `        refuse('unknown or incomplete code_tree keys')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 403 | + | `    archive = read_override_pin(value['archive']); pin = read_override_pin(value['pin'])` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 404 | + | `    code = json.loads(pin.read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 405 | + | `    if set(code) != {'schema', 'commit', 'tree_sha256', 'files', 'sources', 'operation_sources', 'archive'} or code['schema'] != 'c1-sealed-source-v1':` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 406 | + | `        refuse('code pin schema differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 407 | + | `    tree = digest(code['files']); name = 't_' + tree[:16] + '.tar'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 408 | + | `    if code['tree_sha256'] != tree or code['commit'] != 'sha256:' + tree or code['archive'] != dict(path=KIT_LOGICAL + name, sha256=sha(archive)):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 409 | + | `        refuse('code tree/archive identity differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 410 | + | `    members = {}; order = []` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 411 | + | `    with tarfile.open(archive) as tf:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 412 | + | `        for m in tf:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 413 | + | `            if not m.isfile() or not safe_rel(m.name) or m.name in members or m.size > 16_000_000 or (m.uid,m.gid,m.uname,m.gname,m.mtime) != (0,0,'','',0) or m.mode not in (0o644,0o755):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 414 | + | `                refuse('unsafe or nondeterministic source member')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 415 | + | `            order.append(m.name); members[m.name] = hashlib.sha256(tf.extractfile(m).read()).hexdigest()` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 416 | + | `    if order != sorted(order) or members != code['files']: refuse('archive members differ from code pin')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 417 | + | `    for key in ('sources', 'operation_sources'):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 418 | + | `        if not code[key] or any(members.get(n) != h for n,h in code[key].items()): refuse('source closure differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 419 | + | `    if members.get('auth/R0_ROOMS.txt') != H1['r0_rooms']['sha256']: refuse('required member is not sealed in tree')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 420 | + | `    shutil.copyfile(archive, out / 'k' / name); shutil.copyfile(pin, out / 'k/7.json')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 421 | + | `    record = json.loads((kit / 'k/s1_record.json').read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 422 | + | `    record['trees']['trainer'] = dict(commit=code['commit'], file_count=len(members), files=members)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 423 | + | `    write(out / 'k/s1_record.json', record)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 424 | + | `    cur['record'] = dict(file=KIT_LOGICAL + 's1_record.json', sha256=sha(out / 'k/s1_record.json'))` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 425 | + | `    cur['trainer'] = dict(file=code['archive']['path'], sha256=code['archive']['sha256'])` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 426 | + | `    cur['commit'] = code['commit']; cfg['code'] = dict(path=KIT_LOGICAL + '7.json', sha256=sha(out / 'k/7.json'))` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 427 | + | `    launch['source_revision'] = code['commit']; launch['slot']['wall_seconds'] = 46800` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 428 | + | `    if 'archive_record' in value:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 429 | + | `        rec = json.loads(read_override_pin(value['archive_record']).read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 430 | + | `        location = str(archive)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 431 | + | `        if not PART.fullmatch(location): refuse('archive attestation must name the uploaded project archive')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 432 | + | `        if rec.get('status') != 'ARCHIVED' or rec.get('durable') is not True or rec.get('location') != location or rec.get('sha256') != sha(archive) or rec.get('tree_sha256') != tree or rec.get('bytes') != archive.stat().st_size:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 433 | + | `            refuse('archive attestation differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 434 | + | `    else:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 435 | + | `        if over.get('status') == 'READY': refuse('READY needs an off-scratch archive attestation')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 436 | + | `        rec = dict(schema='s1-source-archive-v1', status='PENDING', durable=False,` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 437 | + | `                   sha256=sha(archive), tree_sha256=tree, bytes=archive.stat().st_size)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 438 | + | `    write(out / 'k/archive.json', rec)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 439 | + | `    if '4.json' in over.get('add_k', {}):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 440 | + | `        auth = json.loads((out / 'k/4.json').read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 441 | + | `        if auth.get('source_revision') != code['commit'] or auth.get('config_sha256') != identity(cfg) or auth.get('production_go_granted') is not False or auth.get('wall_seconds') != 46800:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 442 | + | `            refuse('new source needs its own conditional authorization')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 443 | + | `    # Both paths refer to the same inode through c.sh's NR -> X/runs writable bind.` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 444 | + | `    replace_once(out / 'b/r.sh', '    printf \'USR1\\n\' >> "$stop_file"',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 445 | + | `        '    printf \'USR1\\n\' >> "$stop_file"\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 446 | + | `        '    run_dir=$(/usr/bin/python3 -I -c \'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])\' "$HX/k/launch.json")\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 447 | + | `        '    mkdir -p "$run_dir"\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 448 | + | `        '    printf \'USR1\\n\' >> "$run_dir/stop.${SLURM_JOB_ID:-local}.request"')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 449 | + | `    replace_once(out / 'b/h.py', 'except (FileNotFoundError, ProcessLookupError):',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 450 | + | `                 'except (FileNotFoundError, ProcessLookupError, PermissionError):')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 451 | + | `    replace_once(out / 'b/i.py', '        except FileNotFoundError: pass',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 452 | + | `                 '        except (FileNotFoundError, PermissionError): pass')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 453 | + | `    replace_once(out / 'job.sh', '#SBATCH --time=24:00:00', '#SBATCH --time=13:00:00')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 454 | + | `    for before, after in [` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 455 | + | `        ('S=/tmp/jjyeung/okit_$K/root', 'S=/tmp/jjyeung/a_17c4ffa4/root'),` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 456 | + | `        ('NX=/tmp/jjyeung/okit_$K/x_${SLURM_JOB_ID:-local}', 'NX=/tmp/jjyeung/a_17c4ffa4/x_${SLURM_JOB_ID:-local}'),` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 457 | + | `        ('NR=${TK_RUNS_DIR:-/tmp/jjyeung/okit_$K/runs}', 'NR=/tmp/jjyeung/a_17c4ffa4/runs')]:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 458 | + | `        replace_once(out / 'b/c.sh', before, after)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 459 | + | `    replace_once(out / 'b/p0.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.preflight',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 460 | + | `                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.preflight')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 461 | + | `    replace_once(out / 'b/r.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.${1:-x}',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 462 | + | `                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.${1:-x}')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 463 | + | `` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 464 | + | `` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| D0 357 | − | `    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the data-only set ' + str(sorted(set(over['config']) - CONFIG)))` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 468 | + | `    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the admitted set ' + str(sorted(set(over['config']) - CONFIG)))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 475 | + | `    validate_h1(over)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 385 | − | `    changing = bool(over.get('config') or over.get('deployment') or over.get('add_k')` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 497 | + | `    changing = bool(over.get('code_tree') or over.get('config') or over.get('deployment') or over.get('add_k')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 522 | + | `    for name in ('h1', 'milestones'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 523 | + | `        if name in oc: cfg[name] = copy.deepcopy(oc[name])` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 524 | + | `    for name in ('scheduled_sampling', 'recipe'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 525 | + | `        if name in oc:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 526 | + | `            cfg[name] = copy.deepcopy(cfg[name])` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 527 | + | `            for k, v in oc[name].items():` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 528 | + | `                if name == 'recipe' and k == 'scheduled_sampling':` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 529 | + | `                    cfg[name][k] = {**cfg[name][k], **v}` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 530 | + | `                else: cfg[name][k] = copy.deepcopy(v)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 412 | − | `    out.mkdir()` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 533 | + | `    out.mkdir(mode=0o700)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 534 | + | `    if 'code_tree' in over and (out.stat().st_mode & 0o777) != 0o700: refuse('directory mode differs')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 546 | + | `` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 547 | + | `    if 'code_tree' in over:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 548 | + | `        install_code(kit, out, over, cfg, cur, launch)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 448 | − | `    code = json.loads((kit / 'k/7.json').read_text())` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 573 | + | `    code = json.loads((out / 'k/7.json').read_text())` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 452 | − | `                  run_directory=f'/tmp/jjyeung/okit_8865619b/runs/{run}', source_seal={**seal, 'sha256': digest(seal)},` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 577 | + | `                  run_directory=(f'/tmp/jjyeung/a_{run}/runs/{run}' if 'code_tree' in over else f'/tmp/jjyeung/okit_8865619b/runs/{run}'), source_seal={**seal, 'sha256': digest(seal)},` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |

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

`b/c.sh`: Isolate staging, namespace and export roots by run while preserving K and sealed input prefixes.

```diff
--- supplied/b/c.sh
+++ shipped/b/c.sh
@@ -15,11 +15,11 @@
 P=/project/community/jjyeung/c7d31ddd
 RR=runs/aws128p_20261025
 EPOCHS=/home/jjyeung/6d00e578
-S=/tmp/jjyeung/okit_$K/root
+S=/tmp/jjyeung/a_17c4ffa4/root
 U=$S/aws/u
 HM=$HX
-NX=/tmp/jjyeung/okit_$K/x_${SLURM_JOB_ID:-local}
-NR=${TK_RUNS_DIR:-/tmp/jjyeung/okit_$K/runs}
+NX=/tmp/jjyeung/a_17c4ffa4/x_${SLURM_JOB_ID:-local}
+NR=/tmp/jjyeung/a_17c4ffa4/runs
 CUR=$HX/k/0.json
 COMMIT=$(/usr/bin/python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["commit"])' "$CUR")
 tk_step() {
```

`b/p0.sh`: Isolate preflight jobs in the same per-run root.

```diff
--- supplied/b/p0.sh
+++ shipped/b/p0.sh
@@ -6,7 +6,7 @@
 PYTHONPATH="$HX/b" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" \
     /usr/bin/python3 -B "$HX/b/p0.py" "$HX" p --metadata-only
 source "$HX/b/c.sh"
-export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.preflight
+export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.preflight
 trap 'for report in "$NX/o/${SLURM_JOB_ID}".preflight.*.json; do [[ ! -f "$report" ]] || cp "$report" "$HX/o/"; done' EXIT
 tk_stage preflight
 /usr/bin/python3 -I - "$CUR" "$HX" "$NX" "$IN" "$SLURM_JOB_ID" <<'PYINPUTS'
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
@@ -36,7 +39,7 @@
 /usr/bin/python3 -I "$HX/b/g.py" "$HX" "${1:?}"
 export TK_RUNS_DIR="$(/usr/bin/python3 -I -c 'import json,pathlib,sys; print(pathlib.Path(json.load(open(sys.argv[1]))["run_directory"]).parent)' "$HX/k/launch.json")"
 source "$HX/b/c.sh"
-export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.${1:-x}
+export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.${1:-x}
 mkdir -p "$TK_JOBDIR" "$HM/o"
 if [[ "${1:-}" == p ]] && ! /usr/bin/python3 -I -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1])).get("in_job_admission") else 1)' "$HX/k/launch.json"; then
     export TK_LIGHT=1
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
@@ -1,24 +1,39 @@
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
+umask 077
+O=/project/community/jjyeung/okh7
+private_dir() {
+    [[ -d "$1" && ! -L "$1" && "$(stat -c %a -- "$1")" == 700 ]] || {
+        printf 'Directory must be mode 0700; run: chmod 700 -- %q\n' "$1" >&2
+        exit 3
+    }
+}
+private_dir "$O"
+
 export PATH=/usr/local/bin:/usr/bin:/bin
 export TK_JOB_START="$(date +%s)"   # one wall clock for restore, staging, admission and training (job.sh must keep it)
-KH=/project/community/jjyeung/okh7/x_f5c353f7 RUN=/tmp/jjyeung/okit_8865619b/runs/359fcc3c
-RS=/project/community/jjyeung/okh7/r/63e57182 LOG=$KH/o/${SLURM_JOB_ID}.w.steps
+KH=/project/community/jjyeung/okh7/x_4b3114cf RUN=/tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4
+RS=/project/community/jjyeung/okh7/r/766136c1 LOG=$KH/o/${SLURM_JOB_ID}.w.steps
 step() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
 newest() {  # newest verified slot: prints "slot step" (empty if none)
     for s in A B; do [[ -f $RS/$s.json ]] && /usr/bin/python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["slot"], d["step"]) if d.get("verified") is True else None' "$RS/$s.json"; done | sort -k2,2n | tail -1
 }
-mkdir -p /tmp/jjyeung && chmod 700 /tmp/jjyeung && mkdir -p "$RUN" "$RS" "$KH/o"
+# BEGIN directory preflight
+NL=/tmp/jjyeung/a_17c4ffa4
+private_dir "$KH"
+for p in /tmp/jjyeung "$NL" "$NL/runs" "$RUN" "$O/r" "$RS"; do
+    [[ ! -e "$p" && ! -L "$p" ]] || private_dir "$p"
+done
+for p in "$NL/runs"/* "$NL/runs"/.[!.]* "$NL/runs"/..?*; do
+    [[ ! -e "$p" && ! -L "$p" ]] && continue
+    [[ "${p##*/}" == 17c4ffa4 && -d "$p" && ! -L "$p" ]] || { echo 'foreign run directory; refusing' >&2; exit 3; }
+done
+mkdir -p -m 700 /tmp/jjyeung "$NL" "$NL/runs" "$RUN" "$O/r" "$RS" "$KH/o" || exit 3
+for p in "$NL" "$NL/runs" "$RUN" "$RS"; do private_dir "$p"; done
+# END directory preflight
 free_kib=$(df -Pk /tmp | awk 'NR==2 {print $4}')
 step "wrapper start on $(hostname -s); /tmp free $(( free_kib / 1048576 )) GiB; TK_JOB_START=$TK_JOB_START ($(date -u -d @"$TK_JOB_START" +%FT%TZ))"
 # Final review F4: a leg needs about 3.6 TB free at its first save; refuse below 3.8 TB (decimal) in the first minute.
@@ -35,7 +50,7 @@
     || { step "refused: export sessions incomplete for run ${RUN##*/}"; exit 5; }
 step "export sessions present for run ${RUN##*/}"
 # Actual archive contents of every new staging entry, before c.sh extracts them (vt.py; sealed k/0.json pinned inside).
-/usr/bin/python3 -I /project/community/jjyeung/okh7/i_bb09a77d/vt.py "$KH" /project/community/jjyeung/okh7/x_07ca49df/k/0.json > "$KH/o/${SLURM_JOB_ID}.vt.json" 2>&1 \
+/usr/bin/python3 -I /project/community/jjyeung/okh7/i_1be16f28/v.py "$KH" /project/community/jjyeung/okh7/x_07ca49df/k/0.json > "$KH/o/${SLURM_JOB_ID}.vt.json" 2>&1 \
     || { step "refused: staging entry check: $(tail -c 300 "$KH/o/${SLURM_JOB_ID}.vt.json")"; exit 5; }
 step "staging entries verified"
 read -r slot sstep < <(newest || true)
@@ -102,7 +117,7 @@
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

Tests: `evidence/derivation.json`, `evidence/archive_layout.json`, `evidence/stop_bridge/result.json`, `evidence/gate_binding.json`, `evidence/staging_test/result.json`, and `evidence/cpu/fallback_fix2/result.json`. The fixed four-rank chain is prepared in tests/RERUN_CHAIN.sh and has only been syntax-checked; it awaits the operator run outside the socket-restricted sandbox. The step-200 fallback uses a native tiny model and real checkpoint/export serialization with local one-rank collective stand-ins.

The fixed packet requires explicit source authorization, checks final configuration identity and immutable payload sums, stages the routing archive under an opaque name, creates private roots, and isolates preflight/training/export paths by run. `FIX1.md` maps each fix to implementation lines and tests. The identity and admission contract remain unchanged; `REPORT.md` and `evidence/hash_changes_fix1.json` give the current hashes and reasons.

The submitter uses `sbatch -J a15_cot_ap5ee9da63`. The account requires the opaque prefix `a15_cot_ap` followed by the existing job token `5ee9da63`. `ids.json`, its payload copy and `go.template.json` carry the full name. `tools/make_orchard.py` regenerates the submitter, payload sums, deterministic upload archive and embedded transport. `tests/test_visible_names.py` allows the prefix only in the submitter’s job-name argument and rejects it on other visible surfaces; every other forbidden-word check remains active. `evidence/hash_changes_fix2.json` records the affected hashes.

```diff
--- before/payload/s.sh
+++ current/payload/s.sh
@@ -25,4 +25,4 @@
 assert go.get('manifest_sha256')==hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
 sys.path.insert(0,str(k/'b'));import a;a.main(k)
 P
-TZ=UTC env -u TK_JOB_START sbatch -J a_5ee9da63 -o /dev/null -e "$KH/o/%j.err"   -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 13:00:00 --signal=B:USR1@3600 --no-requeue "$BUN/jb.sh"
+TZ=UTC env -u TK_JOB_START sbatch -J a15_cot_ap5ee9da63 -o /dev/null -e "$KH/o/%j.err"   -A mt01 -p advanced -N1 --ntasks=1 --gres=gpu:4 -c 48 --mem=800G -t 13:00:00 --signal=B:USR1@3600 --no-requeue "$BUN/jb.sh"
```

```diff
--- before/tests/test_visible_names.py
+++ current/tests/test_visible_names.py
@@ -7,12 +7,18 @@
 # These exact logical prefixes are bound by the sealed input identities.
 inherited=['/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung','/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung']
 checked=[]
+def visible_line(name,line):
+ # The account mandates this exact prefix only in the submitter's job-name argument.
+ if name=='payload/s.sh':
+  line=re.sub(r'^(TZ=UTC env -u TK_JOB_START sbatch -J )a15_cot_ap(?=[0-9a-f]+(?:\s|$))',r'\1a_',line)
+ return line
 def check(name,text):
  for line in text.splitlines():
   if line.lstrip().startswith('#'):continue
   # Attribute names such as str.split() are code, not visible naming values.
   line=re.sub(r'\.split\(','.operation(',line)
   for prefix in inherited:line=line.replace(prefix,'/sealed/prefix')
+  line=visible_line(name,line)
   assert not forbidden.search(line),(name,line)
  checked.append(name)
 for name in ['orch_h1.sh','fin_h1.sh','payload/o.sh','payload/g.sh','payload/z.sh','payload/s.sh']:
@@ -36,10 +42,33 @@
 assert s.index('r.py copy')<s.index('tar -xf')
 assert 'sha256' in s[:s.index('tar -xf')]
 # Public entrypoint names are opaque; these local delivery filenames are never passed to Orchard.
-assert 'sbatch -J a_5ee9da63' in (H/'payload/s.sh').read_text()
+ids=json.loads((H/'ids.json').read_text());tokens=json.loads((H/'TOKENS_H1.json').read_text())
+assert ids['tokens']==tokens and tokens['job']=='5ee9da63'
+assert ids['job_name']=='a15_cot_ap'+tokens['job']=='a15_cot_ap5ee9da63'
+assert json.loads((H/'payload/ids.json').read_text())==ids
+assert json.loads((H/'payload/go.template.json').read_text())['job_name']==ids['job_name']
+submit=(H/'payload/s.sh').read_text()
+assert re.findall(r'\bsbatch -J (\S+)',submit)==[ids['job_name']]
+command='TZ=UTC env -u TK_JOB_START sbatch -J '
+assert not forbidden.search(visible_line('payload/s.sh',command+ids['job_name']))
+# The exception must not hide other methods, malformed suffixes, paths, logs or env values.
+for name,line in [
+ ('payload/g.sh',command+ids['job_name']),
+ ('payload/s.sh','echo '+ids['job_name']),
+ ('payload/s.sh','JOB='+ids['job_name']),
+ ('payload/s.sh','/tmp/'+ids['job_name']),
+ ('payload/s.sh',command+'a15_cot_ap'),
+ ('payload/s.sh',command+'a15_cot_apxyz'),
+ ('payload/s.sh',command+ids['job_name']+'_cot'),
+ ('payload/s.sh',command+ids['job_name']+' -o /tmp/cot'),
+ ('payload/s.sh',command+'a15_cot_ap_cot5ee9da63'),
+]:
+ assert forbidden.search(visible_line(name,line)),(name,line)
+for word in ('distill','split','vsi','vsibench','revsi','scannet','scannetpp','arkit','arkitscenes','sft','h1','r0','qwen','qwen3.5','cot','vstibench','dsibench'):
+ assert forbidden.search(visible_line('payload/s.sh',command+ids['job_name']+' -o /tmp/'+word)),word
 # Pinned inherited compute-node sources must remain byte-identical.
 old=(D/'kitfull/b/c.sh').read_text();new=(H/'build/fx/b/c.sh').read_text()
 for needle in ['R=/project/community/jjyeung/distill/okit','models--Qwen--Qwen3.5-9B']:
  assert [x for x in old.splitlines() if needle in x]==[x for x in new.splitlines() if needle in x]
-result=dict(status='PASS',surfaces=checked,inherited_exact_prefixes=inherited,scope='New shell argv/path/env/log literals, added runtime lines, and r.py string values. Private trainer contents require separate content review.')
+result=dict(status='PASS',surfaces=checked,inherited_exact_prefixes=inherited,job_name=ids['job_name'],job_prefix_exception='a15_cot_ap only in payload/s.sh sbatch -J with a hex suffix',exception_negative_checks='PASS',scope='New shell argv/path/env/log literals, added runtime lines, and r.py string values. Private trainer contents require separate content review.')
 (H/'evidence/visible_names.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
```
