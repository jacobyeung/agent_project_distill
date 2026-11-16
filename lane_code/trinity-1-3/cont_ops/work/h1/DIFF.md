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
| H1 45 | + | `"""Mode-preserving writes confined to one derived output tree."""` | Document and expose only the declared code-tree and config override fields. |
| H1 46 | + | `from contextlib import contextmanager` | Document and expose only the declared code-tree and config override fields. |
| H1 47 | + | `import stat` | Document and expose only the declared code-tree and config override fields. |
| H1 48 | + | `from pathlib import Path` | Document and expose only the declared code-tree and config override fields. |
| H1 49 | + | `` | Document and expose only the declared code-tree and config override fields. |
| H1 50 | + | `` | Document and expose only the declared code-tree and config override fields. |
| H1 51 | + | `def mode_inventory(root):` | Compare file and directory modes independently of byte hashes. |
| H1 52 | + | `    root = Path(root)` | Compare file and directory modes independently of byte hashes. |
| H1 53 | + | `    return {str(p.relative_to(root)): stat.S_IMODE(p.stat().st_mode)` | Compare file and directory modes independently of byte hashes. |
| H1 54 | + | `            for p in [root, *sorted(root.rglob('*'))]}` | Compare file and directory modes independently of byte hashes. |
| H1 55 | + | `` | Compare file and directory modes independently of byte hashes. |
| H1 56 | + | `` | Compare file and directory modes independently of byte hashes. |
| H1 57 | + | `class SealedOutput:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 58 | + | `    def __init__(self, root, file_mode=0o400):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 59 | + | `        root = Path(root).absolute()` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 60 | + | `        if root != root.resolve(strict=True): refuse('symlink in output root')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 61 | + | `        self.root = root` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 62 | + | `        self.file_mode = file_mode` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 63 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 64 | + | `    def checked(self, path):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 65 | + | `        path = Path(path).absolute()` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 66 | + | `        if (path != self.root and self.root not in path.parents) or '..' in path.parts:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 67 | + | `            refuse('write outside output directory')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 68 | + | `        for p in [path, *path.parents]:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 69 | + | `            if p.is_symlink(): refuse('symlink in output write')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 70 | + | `            if p == self.root: break` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 71 | + | `        if path.is_file() and path.stat().st_nlink != 1:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 72 | + | `            refuse('linked output file')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 73 | + | `        return path` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 74 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 75 | + | `    @contextmanager` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 76 | + | `    def writable(self, path, mode=None):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 77 | + | `        path = self.checked(path)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 78 | + | `        if path == self.root: refuse('write must name an output member')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 79 | + | `        parent = path.parent` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 80 | + | `        parent_mode = stat.S_IMODE(parent.stat().st_mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 81 | + | `        final_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else (` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 82 | + | `            self.file_mode if mode is None else mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 83 | + | `        try:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 84 | + | `            parent.chmod(parent_mode &#124; stat.S_IWUSR)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 85 | + | `            if path.exists(): path.chmod(final_mode &#124; stat.S_IWUSR)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 86 | + | `            yield path` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 87 | + | `        finally:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 88 | + | `            try:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 89 | + | `                if path.exists(): path.chmod(final_mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 90 | + | `            finally:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 91 | + | `                parent.chmod(parent_mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 92 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 93 | + | `    def text(self, path, text, mode=None):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 94 | + | `        with self.writable(path, mode) as p: p.write_text(text)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 95 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 96 | + | `    def write(self, path, value, mode=None):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 97 | + | `        self.text(path, enc(value) + '\n', mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 98 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 99 | + | `    def copy(self, source, path, mode=None):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 100 | + | `        with self.writable(path, mode) as p: shutil.copyfile(source, p)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 101 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 102 | + | `    def mkdir(self, path, mode):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 103 | + | `        with self.writable(path, mode) as p: p.mkdir(mode=mode &#124; stat.S_IWUSR)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 104 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 105 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| D0 51 | − | `       'export_member_names', 'e00_listing'}` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 115 | + | `       'export_member_names', 'e00_listing', 'code_tree'}` | Document and expose only the declared code-tree and config override fields. |
| D0 53 | − | `CONFIG = {'streams', 'init_artifact', 's1_routing'}` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 117 | + | `CONFIG = {'streams', 'init_artifact', 's1_routing', 'h1', 'milestones', 'recipe', 'scheduled_sampling'}` | Document and expose only the declared code-tree and config override fields. |
| H1 285 | + | `    if 'code_tree' in over:` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 286 | + | `        regen &#124;= code_records(json.loads((out / 'k/7.json').read_text()))` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 420 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 421 | + | `# Code changes have a separate validator; data staging never gains executable destinations.` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 422 | + | `H1 = dict(faithful_own_camera_rows=True, routing_pose_targets=True,` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 423 | + | `          camera_types=['camera_displacement', 'camera_movement_direction', 'camera_rotation'],` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 424 | + | `          stop_after_step=200, metrics=True,` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 425 | + | `          r0_rooms=dict(path='auth/R0_ROOMS.txt', sha256='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'))` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 426 | + | `SAMPLING = dict(force_from_step=1, max_own_probability=0.5)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 427 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 428 | + | `def validate_h1(over):` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 429 | + | `    oc = over.get('config', {})` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 430 | + | `    new = set(oc) & {'h1', 'milestones', 'recipe', 'scheduled_sampling'}` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 431 | + | `    if new and 'code_tree' not in over: refuse('new training settings require code_tree')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 432 | + | `    if 'h1' in oc and enc(oc['h1']) != enc(H1): refuse('only the registered settings are admitted')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 433 | + | `    if 'milestones' in oc and enc(oc['milestones']) != enc([100, 200]): refuse('only milestones [100, 200] admitted')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 434 | + | `    for value in [oc.get('scheduled_sampling', {}), oc.get('recipe', {}).get('scheduled_sampling', {})]:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 435 | + | `        if not isinstance(value, dict) or set(value)-set(SAMPLING) or any(enc(value[k]) != enc(SAMPLING[k]) for k in value):` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 436 | + | `            refuse('scheduled_sampling permits only force_from_step=1 and max_own_probability=0.5')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 437 | + | `    if set(oc.get('recipe', {}))-{'milestones', 'scheduled_sampling'}: refuse('unknown recipe keys')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 438 | + | `    if 'milestones' in oc.get('recipe', {}) and oc['recipe']['milestones'] != [100, 200]: refuse('recipe milestones differ')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 439 | + | `    if 'code_tree' in over:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 440 | + | `        if '4.json' not in over.get('add_k', {}): refuse('code_tree requires add_k 4.json')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 441 | + | `        if new != {'h1', 'milestones', 'recipe', 'scheduled_sampling'} or oc['recipe'] != dict(milestones=[100, 200], scheduled_sampling=SAMPLING) or oc['scheduled_sampling'] != SAMPLING:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 442 | + | `            refuse('code_tree requires the complete registered settings')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 443 | + | `` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 444 | + | `def code_records(code):` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 445 | + | `    return {'k/7.json', 'k/s1_record.json', 'k/archive.json', 'k/' + Path(code['archive']['path']).name,` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 446 | + | `            'b/c.sh', 'b/p0.sh', 'b/r.sh', 'b/h.py', 'b/i.py', 'job.sh'}` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 447 | + | `` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 448 | + | `def read_override_pin(value):` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 449 | + | `    if not isinstance(value, dict) or set(value) != {'path', 'sha256'} or not HEX64.fullmatch(str(value['sha256'])):` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 450 | + | `        refuse('malformed code override pin')` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 451 | + | `    if sha(value['path']) != value['sha256']: refuse('code override pin differs')` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 452 | + | `    return Path(value['path'])` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 453 | + | `` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 454 | + | `def replace_once(fs, path, before, after):` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 455 | + | `    text = path.read_text()` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 456 | + | `    if text.count(before) != 1: refuse('fixed runtime patch does not match ' + path.name)` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 457 | + | `    fs.text(path, text.replace(before, after))` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 458 | + | `` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 459 | + | `def install_code(kit, out, over, cfg, cur, launch, fs):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 460 | + | `    if over['run_key'] != '17c4ffa4': refuse('unregistered run')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 461 | + | `    value = over['code_tree']` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 462 | + | `    if not isinstance(value, dict) or set(value)-{'archive', 'pin', 'archive_record'} or not {'archive', 'pin'} <= set(value):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 463 | + | `        refuse('unknown or incomplete code_tree keys')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 464 | + | `    archive = read_override_pin(value['archive']); pin = read_override_pin(value['pin'])` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 465 | + | `    code = json.loads(pin.read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 466 | + | `    if set(code) != {'schema', 'commit', 'tree_sha256', 'files', 'sources', 'operation_sources', 'archive'} or code['schema'] != 'c1-sealed-source-v1':` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 467 | + | `        refuse('code pin schema differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 468 | + | `    tree = digest(code['files']); name = 't_' + tree[:16] + '.tar'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 469 | + | `    if code['tree_sha256'] != tree or code['commit'] != 'sha256:' + tree or code['archive'] != dict(path=KIT_LOGICAL + name, sha256=sha(archive)):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 470 | + | `        refuse('code tree/archive identity differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 471 | + | `    members = {}; order = []` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 472 | + | `    with tarfile.open(archive) as tf:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 473 | + | `        for m in tf:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 474 | + | `            if not m.isfile() or not safe_rel(m.name) or m.name in members or m.size > 16_000_000 or (m.uid,m.gid,m.uname,m.gname,m.mtime) != (0,0,'','',0) or m.mode not in (0o644,0o755):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 475 | + | `                refuse('unsafe or nondeterministic source member')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 476 | + | `            order.append(m.name); members[m.name] = hashlib.sha256(tf.extractfile(m).read()).hexdigest()` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 477 | + | `    if order != sorted(order) or members != code['files']: refuse('archive members differ from code pin')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 478 | + | `    for key in ('sources', 'operation_sources'):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 479 | + | `        if not code[key] or any(members.get(n) != h for n,h in code[key].items()): refuse('source closure differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 480 | + | `    if members.get('auth/R0_ROOMS.txt') != H1['r0_rooms']['sha256']: refuse('required member is not sealed in tree')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 481 | + | `    fs.copy(archive, out / 'k' / name); fs.copy(pin, out / 'k/7.json')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 482 | + | `    record = json.loads((kit / 'k/s1_record.json').read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 483 | + | `    record['trees']['trainer'] = dict(commit=code['commit'], file_count=len(members), files=members)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 484 | + | `    fs.write(out / 'k/s1_record.json', record)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 485 | + | `    cur['record'] = dict(file=KIT_LOGICAL + 's1_record.json', sha256=sha(out / 'k/s1_record.json'))` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 486 | + | `    cur['trainer'] = dict(file=code['archive']['path'], sha256=code['archive']['sha256'])` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 487 | + | `    cur['commit'] = code['commit']; cfg['code'] = dict(path=KIT_LOGICAL + '7.json', sha256=sha(out / 'k/7.json'))` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 488 | + | `    launch['source_revision'] = code['commit']; launch['slot']['wall_seconds'] = 46800` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 489 | + | `    if 'archive_record' in value:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 490 | + | `        rec = json.loads(read_override_pin(value['archive_record']).read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 491 | + | `        location = str(archive)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 492 | + | `        if not PART.fullmatch(location): refuse('archive attestation must name the uploaded project archive')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 493 | + | `        if rec.get('status') != 'ARCHIVED' or rec.get('durable') is not True or rec.get('location') != location or rec.get('sha256') != sha(archive) or rec.get('tree_sha256') != tree or rec.get('bytes') != archive.stat().st_size:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 494 | + | `            refuse('archive attestation differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 495 | + | `    else:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 496 | + | `        if over.get('status') == 'READY': refuse('READY needs an off-scratch archive attestation')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 497 | + | `        rec = dict(schema='s1-source-archive-v1', status='PENDING', durable=False,` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 498 | + | `                   sha256=sha(archive), tree_sha256=tree, bytes=archive.stat().st_size)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 499 | + | `    fs.write(out / 'k/archive.json', rec)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 500 | + | `    if '4.json' in over.get('add_k', {}):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 501 | + | `        auth = json.loads((out / 'k/4.json').read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 502 | + | `        if auth.get('source_revision') != code['commit'] or auth.get('config_sha256') != identity(cfg) or auth.get('production_go_granted') is not False or auth.get('wall_seconds') != 46800:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 503 | + | `            refuse('new source needs its own conditional authorization')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 504 | + | `    # Both paths refer to the same inode through c.sh's NR -> X/runs writable bind.` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 505 | + | `    replace_once(fs, out / 'b/r.sh', '    printf \'USR1\\n\' >> "$stop_file"',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 506 | + | `        '    printf \'USR1\\n\' >> "$stop_file"\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 507 | + | `        '    run_dir=$(/usr/bin/python3 -I -c \'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])\' "$HX/k/launch.json")\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 508 | + | `        '    mkdir -p "$run_dir"\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 509 | + | `        '    printf \'USR1\\n\' >> "$run_dir/stop.${SLURM_JOB_ID:-local}.request"')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 510 | + | `    replace_once(fs, out / 'b/h.py', 'except (FileNotFoundError, ProcessLookupError):',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 511 | + | `                 'except (FileNotFoundError, ProcessLookupError, PermissionError):')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 512 | + | `    replace_once(fs, out / 'b/i.py', '        except FileNotFoundError: pass',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 513 | + | `                 '        except (FileNotFoundError, PermissionError): pass')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 514 | + | `    replace_once(fs, out / 'job.sh', '#SBATCH --time=24:00:00', '#SBATCH --time=13:00:00')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 515 | + | `    for before, after in [` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 516 | + | `        ('S=/tmp/jjyeung/okit_$K/root', 'S=/tmp/jjyeung/a_17c4ffa4/root'),` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 517 | + | `        ('NX=/tmp/jjyeung/okit_$K/x_${SLURM_JOB_ID:-local}', 'NX=/tmp/jjyeung/a_17c4ffa4/x_${SLURM_JOB_ID:-local}'),` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 518 | + | `        ('NR=${TK_RUNS_DIR:-/tmp/jjyeung/okit_$K/runs}', 'NR=/tmp/jjyeung/a_17c4ffa4/runs')]:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 519 | + | `        replace_once(fs, out / 'b/c.sh', before, after)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 520 | + | `    replace_once(fs, out / 'b/p0.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.preflight',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 521 | + | `                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.preflight')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 522 | + | `    replace_once(fs, out / 'b/r.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.${1:-x}',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 523 | + | `                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.${1:-x}')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 524 | + | `` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 525 | + | `` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| D0 357 | − | `    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the data-only set ' + str(sorted(set(over['config']) - CONFIG)))` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 529 | + | `    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the admitted set ' + str(sorted(set(over['config']) - CONFIG)))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 536 | + | `    validate_h1(over)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 385 | − | `    changing = bool(over.get('config') or over.get('deployment') or over.get('add_k')` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 558 | + | `    changing = bool(over.get('code_tree') or over.get('config') or over.get('deployment') or over.get('add_k')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 583 | + | `    for name in ('h1', 'milestones'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 584 | + | `        if name in oc: cfg[name] = copy.deepcopy(oc[name])` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 585 | + | `    for name in ('scheduled_sampling', 'recipe'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 586 | + | `        if name in oc:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 587 | + | `            cfg[name] = copy.deepcopy(cfg[name])` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 588 | + | `            for k, v in oc[name].items():` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 589 | + | `                if name == 'recipe' and k == 'scheduled_sampling':` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 590 | + | `                    cfg[name][k] = {**cfg[name][k], **v}` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 591 | + | `                else: cfg[name][k] = copy.deepcopy(v)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 412 | − | `    out.mkdir()` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 594 | + | `    # Copy only regular files/directories; never follow a sealed link into another tree.` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 595 | + | `    for p in kit.rglob('*'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 596 | + | `        if p.is_symlink() or not (p.is_file() or p.is_dir()): refuse('unsupported source member')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 597 | + | `    out.mkdir(mode=0o700)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 598 | + | `    fs = SealedOutput(out, stat.S_IMODE((kit / 'k/1.json').stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 599 | + | `    if 'code_tree' in over and (out.stat().st_mode & 0o777) != 0o700: refuse('directory mode differs')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 415 | − | `    (out / 'k').mkdir(); (out / 'o').mkdir(); (out / 'runs').mkdir()` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 602 | + | `    for name in ('k', 'o', 'runs'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 603 | + | `        if not changing and not (kit / name).exists(): continue` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 604 | + | `        mode = stat.S_IMODE((kit / name).stat().st_mode) if (kit / name).exists() else 0o700` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 605 | + | `        fs.mkdir(out / name, mode)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 417 | − | `        if p.name in ('launch.json', '1.json', '0.json', old_key + '.json'): continue` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 418 | − | `        shutil.copy2(p, out / 'k' / p.name)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 607 | + | `        if p.name == old_key + '.json' and changing: continue` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 608 | + | `        fs.copy(p, out / 'k' / p.name, stat.S_IMODE(p.stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 421 | − | `        shutil.copyfile(pin['path'], out / 'k' / name)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 611 | + | `        fs.copy(pin['path'], out / 'k' / name)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 614 | + | `` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 615 | + | `    if 'code_tree' in over:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 616 | + | `        install_code(kit, out, over, cfg, cur, launch, fs)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 445 | − | `    write(out / 'k' / (key + '.json'), cfg)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 446 | − | `    write(out / 'k/1.json', {'0': key})` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 447 | − | `    write(out / 'k/0.json', cur)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 448 | − | `    code = json.loads((kit / 'k/7.json').read_text())` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 638 | + | `    fs.write(out / 'k' / (key + '.json'), cfg, stat.S_IMODE((kit / 'k' / (old_key + '.json')).stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 639 | + | `    fs.write(out / 'k/1.json', {'0': key})` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 640 | + | `    fs.write(out / 'k/0.json', cur)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 641 | + | `    code = json.loads((out / 'k/7.json').read_text())` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 452 | − | `                  run_directory=f'/tmp/jjyeung/okit_8865619b/runs/{run}', source_seal={**seal, 'sha256': digest(seal)},` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 645 | + | `                  run_directory=(f'/tmp/jjyeung/a_{run}/runs/{run}' if 'code_tree' in over else f'/tmp/jjyeung/okit_8865619b/runs/{run}'), source_seal={**seal, 'sha256': digest(seal)},` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 479 | − | `    write(out / 'k/launch.json', launch)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 672 | + | `    fs.write(out / 'k/launch.json', launch)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 483 | − | `    (out / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(inventory.items())))` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 676 | + | `    fs.text(out / 'SHA256SUMS.txt', ''.join(f'{v}  {k}\n' for k, v in sorted(inventory.items())), stat.S_IMODE((kit / 'SHA256SUMS.txt').stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 677 | + | `    if (kit / 'ANON_OK.json').is_file():` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 678 | + | `        fs.copy(kit / 'ANON_OK.json', out / 'ANON_OK.json', stat.S_IMODE((kit / 'ANON_OK.json').stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 485 | − | `        write(out / 'ANON_OK.json', dict(status='UNREVIEWED', hits=None, manifest_sha256=sha(out / 'SHA256SUMS.txt'), external=[],` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 680 | + | `        fs.write(out / 'ANON_OK.json', dict(status='UNREVIEWED', hits=None, manifest_sha256=sha(out / 'SHA256SUMS.txt'), external=[],` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 682 | + | `    if not changing: out.chmod(stat.S_IMODE(kit.stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |

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

Tests: `evidence/derivation.json`, `evidence/archive_layout.json`, `evidence/stop_bridge/result.json`, `evidence/gate_binding.json`, `evidence/staging_test/result.json`, and `evidence/cpu/fallback_fix3/result.json`. The fixed four-rank chain is prepared in tests/RERUN_CHAIN.sh and has only been syntax-checked; it awaits the operator run outside the socket-restricted sandbox. The step-200 fallback uses a native tiny model and real checkpoint/export serialization with local one-rank collective stand-ins.

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

Sealed-mode writes restore each output file and parent directory in finally blocks. Empty reproduction and final comparison check modes separately from SHA256SUMS. FIX3.md lists every audited write; evidence/fix3_modes.json records the old-code failure and the passing regressions.

```diff
--- round2/tools/make_deriver.py
+++ current/tools/make_deriver.py
@@ -123,4 +123,31 @@
 s=s.replace("    out.mkdir()", "    out.mkdir(mode=0o700)\n    if 'code_tree' in over and (out.stat().st_mode & 0o777) != 0o700: refuse('directory mode differs')")
 s=s.replace("run_directory=f'/tmp/jjyeung/okit_8865619b/runs/{run}'", "run_directory=(f'/tmp/jjyeung/a_{run}/runs/{run}' if 'code_tree' in over else f'/tmp/jjyeung/okit_8865619b/runs/{run}')")
 s=s.replace('only the registered h1 block is admitted', 'only the registered settings are admitted').replace('R0 rooms not sealed in tree', 'required member is not sealed in tree')
+# Every mutation of the copied kit goes through an output-scoped writer.
+mode_helpers = Path('tools/sealed_output.py').read_text()
+s=s.replace('\ndef identity(cfg):', '\n' + mode_helpers + '\n\ndef identity(cfg):')
+s=s.replace('def replace_once(path, before, after):', 'def replace_once(fs, path, before, after):')
+s=s.replace('    path.write_text(text.replace(before, after))', '    fs.text(path, text.replace(before, after))')
+s=s.replace('replace_once(out /', 'replace_once(fs, out /')
+s=s.replace('def install_code(kit, out, over, cfg, cur, launch):', 'def install_code(kit, out, over, cfg, cur, launch, fs):')
+s=s.replace('install_code(kit, out, over, cfg, cur, launch)', 'install_code(kit, out, over, cfg, cur, launch, fs)')
+s=s.replace('shutil.copyfile(archive, out /', 'fs.copy(archive, out /')
+s=s.replace('shutil.copyfile(pin, out /', 'fs.copy(pin, out /')
+s=s.replace("shutil.copyfile(pin['path'], out /", "fs.copy(pin['path'], out /")
+s=s.replace('write(out /', 'fs.write(out /')
+s=s.replace("    out.mkdir(mode=0o700)", """    # Copy only regular files/directories; never follow a sealed link into another tree.
+    for p in kit.rglob('*'):
+        if p.is_symlink() or not (p.is_file() or p.is_dir()): refuse('unsupported source member')
+    out.mkdir(mode=0o700)
+    fs = SealedOutput(out, stat.S_IMODE((kit / 'k/1.json').stat().st_mode))""")
+s=s.replace("    (out / 'k').mkdir(); (out / 'o').mkdir(); (out / 'runs').mkdir()", """    for name in ('k', 'o', 'runs'):
+        if not changing and not (kit / name).exists(): continue
+        mode = stat.S_IMODE((kit / name).stat().st_mode) if (kit / name).exists() else 0o700
+        fs.mkdir(out / name, mode)""")
+s=s.replace("        if p.name in ('launch.json', '1.json', '0.json', old_key + '.json'): continue\n        shutil.copy2(p, out / 'k' / p.name)", """        if p.name == old_key + '.json' and changing: continue
+        fs.copy(p, out / 'k' / p.name, stat.S_IMODE(p.stat().st_mode))""")
+s=s.replace("fs.write(out / 'k' / (key + '.json'), cfg)", "fs.write(out / 'k' / (key + '.json'), cfg, stat.S_IMODE((kit / 'k' / (old_key + '.json')).stat().st_mode))")
+s=s.replace("    (out / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\\n' for k, v in sorted(inventory.items())))", "    fs.text(out / 'SHA256SUMS.txt', ''.join(f'{v}  {k}\\n' for k, v in sorted(inventory.items())), stat.S_IMODE((kit / 'SHA256SUMS.txt').stat().st_mode))")
+s=s.replace("    if changing:  # explicit placeholder", "    if (kit / 'ANON_OK.json').is_file():\n        fs.copy(kit / 'ANON_OK.json', out / 'ANON_OK.json', stat.S_IMODE((kit / 'ANON_OK.json').stat().st_mode))\n    if changing:  # explicit placeholder")
+s=s.replace('    return dict(config_key=key,', "    if not changing: out.chmod(stat.S_IMODE(kit.stat().st_mode))\n    return dict(config_key=key,")
 Path('tools/derive_kit_h1.py').write_text(s)
```

```diff
--- round2/tools/orchard_records.py
+++ current/tools/orchard_records.py
@@ -48,11 +48,13 @@
  sys.path.insert(0,str(B/'p/b'));from d import contract
  la=load(B/'p/k/launch.json');cfg=load(B/'p'/la['config']['file'])
  assert result['config_identity']==ids['identity'] and dk.digest(contract(la,cfg))==ids['contract']
- # Reproduce the complete source kit with empty overrides; all manifest members must be byte-identical.
+ # Reproduce the complete source kit with empty overrides, including member modes.
  dk.derive(base,B/'e',{})
  assert manifest(B/'e')==manifest(base)
  for n,h in manifest(base).items():assert dk.sha(B/'e'/n)==h
- w(B/'e.json',dict(status='PASS',manifest_sha256=dk.sha(base/'SHA256SUMS.txt')))
+ actual=dk.mode_inventory(B/'e');expected=dk.mode_inventory(base)
+ assert actual==expected, 'member modes differ'
+ w(B/'e.json',dict(status='PASS',manifest_sha256=dk.sha(base/'SHA256SUMS.txt'),modes_sha256=dk.digest(expected)))
 elif mode=='stage':
  spec=importlib.util.spec_from_file_location('verify',B/'v.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
  checks=v.main(B/'p',base/'k/0.json');w(B/'c.json',checks)
@@ -75,17 +77,18 @@
  w(B/'result.json',r)
  # Compare the complete final inventory to a complete temporary derivation, not a FIXTURE launch hash.
  candidate=B/'q';test=dict(o,fixture=True,status='BLOCKED');dk.derive(base,candidate,test)
- la=load(candidate/'k/launch.json');la.update(status='READY',production_authorized=True);w(candidate/'k/launch.json',la)
+ la=load(candidate/'k/launch.json');la.update(status='READY',production_authorized=True);dk.SealedOutput(candidate).write(candidate/'k/launch.json',la)
  man=manifest(candidate);man['k/launch.json']=dk.sha(candidate/'k/launch.json')
  assert man==manifest(KH)
+ assert dk.mode_inventory(candidate)==dk.mode_inventory(KH), 'member modes differ'
  # Separate ANON content review must cover these exact bytes; never manufacture CLEAN here.
  names={line.split('  ',1)[1] for line in (B/'sums.txt').read_text().splitlines()} | {'ready.json','archive.json','gate.json','c.json','e.json'}
  external=[dict(path=str(B/n),sha256=dk.sha(B/n)) for n in sorted(names)]
  w(B/'anon.json',dict(status='UNREVIEWED',hits=None,manifest_sha256=dk.sha(KH/'SHA256SUMS.txt'),external=external,scope='Final changed records, runtime scripts and trainer contents require content review; inherited identifiers need explicit accounting. This record grants no submission approval.'))
- w(B/'compare.json',dict(status='PASS',manifest_sha256=dk.sha(KH/'SHA256SUMS.txt'),identity=r['config_identity'],contract=ids['contract'],config_key=r['config_key']))
+ w(B/'compare.json',dict(status='PASS',manifest_sha256=dk.sha(KH/'SHA256SUMS.txt'),identity=r['config_identity'],contract=ids['contract'],config_key=r['config_key'],modes_sha256=dk.digest(dk.mode_inventory(KH))))
 elif mode=='certify':
  cert=load(B/'anon.json');assert cert['status']=='CLEAN' and cert['hits']==0 and cert['manifest_sha256']==dk.sha(KH/'SHA256SUMS.txt')
  for p in cert['external']:assert dk.sha(p['path'])==p['sha256']
- w(KH/'ANON_OK.json',cert)
+ dk.SealedOutput(KH).write(KH/'ANON_OK.json',cert)
  sys.path.insert(0,str(KH/'b'));import a;a.main(KH)
 else:raise SystemExit('unknown mode')
```

```diff
--- round2/tools/sealed_output.py
+++ current/tools/sealed_output.py
@@ -0,0 +1,59 @@
+"""Mode-preserving writes confined to one derived output tree."""
+from contextlib import contextmanager
+import stat
+from pathlib import Path
+
+
+def mode_inventory(root):
+    root = Path(root)
+    return {str(p.relative_to(root)): stat.S_IMODE(p.stat().st_mode)
+            for p in [root, *sorted(root.rglob('*'))]}
+
+
+class SealedOutput:
+    def __init__(self, root, file_mode=0o400):
+        root = Path(root).absolute()
+        if root != root.resolve(strict=True): refuse('symlink in output root')
+        self.root = root
+        self.file_mode = file_mode
+
+    def checked(self, path):
+        path = Path(path).absolute()
+        if (path != self.root and self.root not in path.parents) or '..' in path.parts:
+            refuse('write outside output directory')
+        for p in [path, *path.parents]:
+            if p.is_symlink(): refuse('symlink in output write')
+            if p == self.root: break
+        if path.is_file() and path.stat().st_nlink != 1:
+            refuse('linked output file')
+        return path
+
+    @contextmanager
+    def writable(self, path, mode=None):
+        path = self.checked(path)
+        if path == self.root: refuse('write must name an output member')
+        parent = path.parent
+        parent_mode = stat.S_IMODE(parent.stat().st_mode)
+        final_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else (
+            self.file_mode if mode is None else mode)
+        try:
+            parent.chmod(parent_mode | stat.S_IWUSR)
+            if path.exists(): path.chmod(final_mode | stat.S_IWUSR)
+            yield path
+        finally:
+            try:
+                if path.exists(): path.chmod(final_mode)
+            finally:
+                parent.chmod(parent_mode)
+
+    def text(self, path, text, mode=None):
+        with self.writable(path, mode) as p: p.write_text(text)
+
+    def write(self, path, value, mode=None):
+        self.text(path, enc(value) + '\n', mode)
+
+    def copy(self, source, path, mode=None):
+        with self.writable(path, mode) as p: shutil.copyfile(source, p)
+
+    def mkdir(self, path, mode):
+        with self.writable(path, mode) as p: p.mkdir(mode=mode | stat.S_IWUSR)
```

```diff
--- round2/tests/test_sealed_modes.py
+++ current/tests/test_sealed_modes.py
@@ -0,0 +1,156 @@
+"""Exercise full derivation with sealed permissions, using only local CPU fixtures."""
+import copy, hashlib, importlib.util, json, os, shutil, stat, sys, subprocess
+from pathlib import Path
+
+H = Path(__file__).resolve().parents[1]
+D = Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0')
+sys.path.insert(0, str(H / 'tools'))
+import derive_kit_h1 as dk
+
+root = H / 'evidence/fix3_modes'
+root.mkdir()
+assert os.geteuid() != 0, 'Permission regression must run without root privileges'
+def load_module(path):
+    spec = importlib.util.spec_from_file_location('old_deriver', path)
+    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
+    return mod
+old = load_module(H / 'evidence/fix3_before/tools/derive_kit_h1.py')
+def snapshot(path):
+    return {str(p.relative_to(path)): [stat.S_IMODE(p.stat().st_mode),
+            dk.sha(p) if p.is_file() else None] for p in [path, *sorted(path.rglob('*'))]}
+def seal(kit, all_members=False):
+    for p in kit.rglob('*'):
+        if all_members or (p == kit / 'b' or kit / 'b' in p.parents):
+            p.chmod(0o500 if p.is_dir() else 0o400)
+    kit.chmod(0o700)
+def validate_files(out):
+    for line in (out / 'SHA256SUMS.txt').read_text().splitlines():
+        h, n = line.split('  ', 1)
+        assert dk.sha(out / n) == h, n
+def unchanged_modes(kit, out):
+    before, after = snapshot(kit), snapshot(out)
+    for n, (mode, digest) in before.items():
+        if n in after and (digest is None or digest == after[n][1]):
+            assert after[n][0] == mode, n
+def contract(out):
+    mod = load_module(out / 'b/d.py')
+    la = json.loads((out / 'k/launch.json').read_text())
+    cfg = json.loads((out / la['config']['file']).read_text())
+    return dk.digest(mod.contract(la, cfg))
+
+# Complete stand-in: only the two unavailable payload bytes and manifest pin differ.
+# This does not claim reproduction of the unavailable complete production kit.
+seed = root / 'seed'; shutil.copytree(D / 'kitfull', seed)
+lines = (seed / 'SHA256SUMS.txt').read_text().splitlines(); synthetic = []
+for i, line in enumerate(lines):
+    h, n = line.split('  ', 1)
+    if not (seed / n).exists():
+        (seed / n).write_bytes(b'local unavailable-payload stand-in\n')
+        lines[i] = dk.sha(seed / n) + '  ' + n; synthetic.append(n)
+assert len(synthetic) == 2
+(seed / 'SHA256SUMS.txt').write_text('\n'.join(lines) + '\n')
+dk.SEALED_MANIFEST = old.SEALED_MANIFEST = dk.sha(seed / 'SHA256SUMS.txt')
+h1 = json.loads((H / 'build/over_local.json').read_text()); h1.pop('fixture', None)
+d0 = json.loads((D / 'a2/v5b/over_fx.json').read_text().replace(
+    '/scratch/jjyeung/orch_n30/cont_ops/work/d0', str(D)))
+d0.pop('fixture', None)
+for h, p in d0['content'].items():
+    if not Path(p).is_absolute(): d0['content'][h] = str(D / 'a2' / p)
+ids = json.loads((H / 'ids.json').read_text())
+result = {'synthetic_missing_payloads': synthetic, 'cases': {}}
+for label, all_members in [('orchard', False), ('fully_sealed', True)]:
+    kit = root / label; shutil.copytree(seed, kit); seal(kit, all_members)
+    before = snapshot(kit)
+    try: old.derive(kit, root / (label + '_round2'), copy.deepcopy(h1))
+    except PermissionError as e:
+        assert str(e.filename).endswith('/b/r.sh') if not all_members else True
+        result['cases'][label + '_round2'] = {'expected_failure': str(e)}
+    else: raise AssertionError('round-2 code unexpectedly accepted sealed writes')
+    for name, overrides in [('h1', h1), ('d0', d0), ('empty', {})]:
+        out = root / (label + '_' + name)
+        r = dk.derive(kit, out, copy.deepcopy(overrides)); validate_files(out)
+        unchanged_modes(kit, out)
+        for n in ('b/r.sh', 'b/h.py', 'b/i.py', 'b/c.sh', 'b/p0.sh', 'job.sh'):
+            assert (out / n).stat().st_mode == (kit / n).stat().st_mode
+        if name == 'empty':
+            actual = snapshot(out)
+            assert actual == before
+            assert (out / 'SHA256SUMS.txt').read_bytes() == (kit / 'SHA256SUMS.txt').read_bytes()
+        elif name == 'h1':
+            assert r['config_identity'] == ids['identity'] and contract(out) == ids['contract']
+        else:
+            assert r['config_identity'].startswith('80f4af94') and contract(out).startswith('aaf2d7b0')
+        assert snapshot(kit) == before, 'source bytes or modes changed'
+        result['cases'][label + '_' + name] = {'status': 'PASS', 'identity': r['config_identity'],
+            'modes_sha256': dk.digest(dk.mode_inventory(out))}
+
+# New files/directories, failure restoration and out-of-tree guards.
+out = root / 'fully_sealed_h1'; fs = dk.SealedOutput(out)
+parent = out / 'b/sa'; before = snapshot(parent)
+fs.text(parent / 'new.json', '{}\n', 0o400)
+fs.mkdir(parent / 'new', 0o500); fs.text(parent / 'new/data', 'new\n')
+assert (parent / 'new.json').stat().st_mode & 0o777 == 0o400
+assert (parent / 'new').stat().st_mode & 0o777 == 0o500
+assert parent.stat().st_mode & 0o777 == 0o500
+p = out / 'b/r.sh'; modes = dk.mode_inventory(out)
+try:
+    with fs.writable(p):
+        assert p.stat().st_mode & 0o200 and p.parent.stat().st_mode & 0o200
+        raise RuntimeError('injected write failure')
+except RuntimeError: pass
+assert dk.mode_inventory(out) == modes
+external = root / 'external'; external.write_text('unchanged'); external.chmod(0o400)
+outside = snapshot(external.parent)['external']
+link = out / 'link'; link.symlink_to(external)
+dirlink = out / 'dirlink'; dirlink.symlink_to(root, target_is_directory=True)
+for target in [external, link, dirlink / 'external', out / '..' / 'external']:
+    try: fs.text(target, 'bad')
+    except ValueError: pass
+    else: raise AssertionError('outside/link write admitted')
+assert [stat.S_IMODE(external.stat().st_mode), dk.sha(external)] == outside
+result['guards_and_restore'] = 'PASS'
+# Run the shipped prepare entry with only physical paths and the synthetic pin relocated.
+bundle = root / 'entry'; bundle.mkdir(mode=0o700)
+base = bundle / 'x_07ca49df'; shutil.copytree(root / 'fully_sealed', base)
+packet = bundle / 'i_1be16f28'; packet.mkdir(mode=0o700)
+source = (H / 'tools/derive_kit_h1.py').read_text().replace(
+    "SEALED_MANIFEST = 'de6e7e0fac4036889fb4112792fbaa2d6f362a0cde09722ba6e93a6a39e7f32b'",
+    'SEALED_MANIFEST = ' + repr(dk.SEALED_MANIFEST))
+(packet / 'd.py').write_text(source)
+record_source = (H / 'tools/orchard_records.py').read_text()
+(packet / 'r.py').write_text(record_source.replace(
+    "O=Path('/project/community/jjyeung/okh7')", 'O=Path(' + repr(str(bundle)) + ')'))
+(packet / 'ids.json').write_text(json.dumps(ids))
+(packet / 'over.json').write_text(json.dumps(h1))
+rc = subprocess.run([sys.executable, '-B', str(packet / 'r.py'), 'prepare'], capture_output=True, text=True)
+assert rc.returncode == 0, rc.stderr
+assert json.loads((packet / 'e.json').read_text())['modes_sha256'] == dk.digest(dk.mode_inventory(base))
+# Execute the exact final comparison block against a sealed candidate and final kit.
+final = root / 'final'; final_over = dict(h1, fixture=True, status='BLOCKED')
+dk.derive(base, final, final_over)
+la = json.loads((final / 'k/launch.json').read_text()); la.update(status='READY', production_authorized=True)
+dk.SealedOutput(final).write(final / 'k/launch.json', la)
+def manifest(root):
+    return dict(reversed(line.split('  ', 1)) for line in (root / 'SHA256SUMS.txt').read_text().splitlines())
+man = manifest(final); man['k/launch.json'] = dk.sha(final / 'k/launch.json')
+dk.SealedOutput(final).text(final / 'SHA256SUMS.txt', ''.join(h + '  ' + n + '\n' for n, h in sorted(man.items())))
+start = record_source.index(' # Compare the complete'); end = record_source.index(' # Separate ANON', start)
+block = '\n'.join(line[1:] for line in record_source[start:end].splitlines())
+scope = dict(B=packet, o=h1, dk=dk, base=base, KH=final, manifest=manifest,
+             load=lambda p: json.loads(p.read_text()))
+exec(block, scope)
+assert (packet / 'q/k/launch.json').stat().st_mode & 0o777 == 0o400
+# A mode-only difference must fail the shipped final comparison despite equal byte manifests.
+mode_line = next(line.strip() for line in block.splitlines() if 'assert dk.mode_inventory' in line)
+(final / 'b/r.sh').chmod(0o600)
+try: exec(mode_line, scope)
+except AssertionError: pass
+else: raise AssertionError('mode-only mismatch accepted')
+(final / 'b/r.sh').chmod(0o400)
+# Certification must also replace a sealed existing certificate without changing its mode.
+cert_line = next(line.strip() for line in record_source.splitlines() if "dk.SealedOutput(KH).write" in line)
+exec(cert_line, dict(dk=dk, KH=final, cert={'status': 'TEST'}))
+assert (final / 'ANON_OK.json').stat().st_mode & 0o777 == 0o400
+result['prepare_final_and_certify_writes'] = 'PASS'
+(H / 'evidence/fix3_modes.json').write_text(json.dumps(result, indent=2) + '\n')
+print(json.dumps(result, indent=2))
```
