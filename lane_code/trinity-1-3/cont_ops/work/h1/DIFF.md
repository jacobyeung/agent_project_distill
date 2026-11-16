The login gate mounts missing logical parents inside bubblewrap and validates a fresh gate.json before reporting its verdict. It reuses t/u only after archive-content and receipt/SQLite verification. `payload/g.sh` is the only changed deployed executable. `tools/make_orchard.py` now packages that canonical script; `tools/build_gate_patch.py` builds the required two-file update. Tests, packaging checks, reports and generated transport/checksums account for the remaining changes.

The exact gate and generator diff is [evidence/gate_fix5.patch](evidence/gate_fix5.patch). [FIX5.md](FIX5.md) maps changes to lines, tests and hashes. The patch keeps the prepared evidence and all downstream derivation/certification/submission bindings consistent; no full re-upload is required before gate/final evidence exists. Configuration identity, admission contract, trainer and fixture manifest remain unchanged.

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
| H1 51 | + | `def manifest_members(root):` | Read and validate the sealed member names without traversing source runtime state. |
| H1 52 | + | `    """Read the sealed member names without walking the surrounding runtime tree."""` | Read and validate the sealed member names without traversing source runtime state. |
| H1 53 | + | `    names = []` | Read and validate the sealed member names without traversing source runtime state. |
| H1 54 | + | `    for line in (Path(root) / 'SHA256SUMS.txt').read_text().splitlines():` | Read and validate the sealed member names without traversing source runtime state. |
| H1 55 | + | `        digest_, name = line.split('  ', 1)` | Read and validate the sealed member names without traversing source runtime state. |
| H1 56 | + | `        if (len(digest_) != 64 or any(c not in '0123456789abcdef' for c in digest_)` | Read and validate the sealed member names without traversing source runtime state. |
| H1 57 | + | `                or name.startswith('/') or any(p in ('', '.', '..') for p in name.split('/'))` | Read and validate the sealed member names without traversing source runtime state. |
| H1 58 | + | `                or name in names):` | Read and validate the sealed member names without traversing source runtime state. |
| H1 59 | + | `            raise ValueError('invalid sealed member')` | Read and validate the sealed member names without traversing source runtime state. |
| H1 60 | + | `        names.append(name)` | Read and validate the sealed member names without traversing source runtime state. |
| H1 61 | + | `    return sorted(names)` | Read and validate the sealed member names without traversing source runtime state. |
| H1 62 | + | `` | Read and validate the sealed member names without traversing source runtime state. |
| H1 63 | + | `` | Read and validate the sealed member names without traversing source runtime state. |
| H1 64 | + | `def member_directories(names):` | Compute only the ancestors of manifest members and the root. |
| H1 65 | + | `    return {'.'} &#124; {str(p) for name in names for p in Path(name).parents}` | Compute only the ancestors of manifest members and the root. |
| H1 66 | + | `` | Compute only the ancestors of manifest members and the root. |
| H1 67 | + | `` | Compute only the ancestors of manifest members and the root. |
| H1 68 | + | `def mode_inventory(root):` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 69 | + | `    root = Path(root)` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 70 | + | `    names = manifest_members(root)` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 71 | + | `    dirs = member_directories(names)` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 72 | + | `    modes = {}` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 73 | + | `    for name in sorted(set(names) &#124; dirs, key=lambda n: (len(Path(n).parts), n)):` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 74 | + | `        mode = (root / name).lstat().st_mode` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 75 | + | `        if not (stat.S_ISDIR(mode) if name in dirs else stat.S_ISREG(mode)):` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 76 | + | `            raise ValueError('unsupported sealed member: ' + name)` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 77 | + | `        modes[name] = stat.S_IMODE(mode)` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 78 | + | `    return modes` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 79 | + | `` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 80 | + | `` | Compare only manifest-member and ancestor-directory modes, excluding runtime state. |
| H1 81 | + | `class SealedOutput:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 82 | + | `    def __init__(self, root, file_mode=0o400):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 83 | + | `        root = Path(root).absolute()` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 84 | + | `        if root != root.resolve(strict=True): refuse('symlink in output root')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 85 | + | `        self.root = root` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 86 | + | `        self.file_mode = file_mode` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 87 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 88 | + | `    def checked(self, path):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 89 | + | `        path = Path(path).absolute()` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 90 | + | `        if (path != self.root and self.root not in path.parents) or '..' in path.parts:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 91 | + | `            refuse('write outside output directory')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 92 | + | `        for p in [path, *path.parents]:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 93 | + | `            if p.is_symlink(): refuse('symlink in output write')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 94 | + | `            if p == self.root: break` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 95 | + | `        if path.is_file() and path.stat().st_nlink != 1:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 96 | + | `            refuse('linked output file')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 97 | + | `        return path` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 98 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 99 | + | `    @contextmanager` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 100 | + | `    def writable(self, path, mode=None):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 101 | + | `        path = self.checked(path)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 102 | + | `        if path == self.root: refuse('write must name an output member')` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 103 | + | `        parent = path.parent` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 104 | + | `        parent_mode = stat.S_IMODE(parent.stat().st_mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 105 | + | `        final_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else (` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 106 | + | `            self.file_mode if mode is None else mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 107 | + | `        try:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 108 | + | `            parent.chmod(parent_mode &#124; stat.S_IWUSR)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 109 | + | `            if path.exists(): path.chmod(final_mode &#124; stat.S_IWUSR)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 110 | + | `            yield path` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 111 | + | `        finally:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 112 | + | `            try:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 113 | + | `                if path.exists(): path.chmod(final_mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 114 | + | `            finally:` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 115 | + | `                parent.chmod(parent_mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 116 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 117 | + | `    def text(self, path, text, mode=None):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 118 | + | `        with self.writable(path, mode) as p: p.write_text(text)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 119 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 120 | + | `    def write(self, path, value, mode=None):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 121 | + | `        self.text(path, enc(value) + '\n', mode)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 122 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 123 | + | `    def copy(self, source, path, mode=None):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 124 | + | `        with self.writable(path, mode) as p: shutil.copyfile(source, p)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 125 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 126 | + | `    def mkdir(self, path, mode):` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 127 | + | `        with self.writable(path, mode) as p: p.mkdir(mode=mode &#124; stat.S_IWUSR)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 128 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 129 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| D0 51 | − | `       'export_member_names', 'e00_listing'}` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 139 | + | `       'export_member_names', 'e00_listing', 'code_tree'}` | Document and expose only the declared code-tree and config override fields. |
| D0 53 | − | `CONFIG = {'streams', 'init_artifact', 's1_routing'}` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 141 | + | `CONFIG = {'streams', 'init_artifact', 's1_routing', 'h1', 'milestones', 'recipe', 'scheduled_sampling'}` | Document and expose only the declared code-tree and config override fields. |
| H1 309 | + | `    if 'code_tree' in over:` | Retain data placement checks while treating validated code records as regenerated kit records. |
| H1 310 | + | `        regen &#124;= code_records(json.loads((out / 'k/7.json').read_text()))` | Retain data placement checks while treating validated code records as regenerated kit records. |
| D0 327 | − | `        [json.loads(p.read_text()) for p in sorted((kit / 'k').iterdir()) if p.suffix == '.json' and p.is_file()])` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 417 | + | `        [json.loads((kit / n).read_text()) for n in manifest_members(kit) if n.startswith('k/') and n.endswith('.json') and n not in missing])` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 444 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 445 | + | `# Code changes have a separate validator; data staging never gains executable destinations.` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 446 | + | `H1 = dict(faithful_own_camera_rows=True, routing_pose_targets=True,` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 447 | + | `          camera_types=['camera_displacement', 'camera_movement_direction', 'camera_rotation'],` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 448 | + | `          stop_after_step=200, metrics=True,` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 449 | + | `          r0_rooms=dict(path='auth/R0_ROOMS.txt', sha256='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'))` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 450 | + | `SAMPLING = dict(force_from_step=1, max_own_probability=0.5)` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 451 | + | `` | Confine mutations to the output tree and restore exact file and parent modes even on failure. |
| H1 452 | + | `def validate_h1(over):` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 453 | + | `    oc = over.get('config', {})` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 454 | + | `    new = set(oc) & {'h1', 'milestones', 'recipe', 'scheduled_sampling'}` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 455 | + | `    if new and 'code_tree' not in over: refuse('new training settings require code_tree')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 456 | + | `    if 'h1' in oc and enc(oc['h1']) != enc(H1): refuse('only the registered settings are admitted')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 457 | + | `    if 'milestones' in oc and enc(oc['milestones']) != enc([100, 200]): refuse('only milestones [100, 200] admitted')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 458 | + | `    for value in [oc.get('scheduled_sampling', {}), oc.get('recipe', {}).get('scheduled_sampling', {})]:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 459 | + | `        if not isinstance(value, dict) or set(value)-set(SAMPLING) or any(enc(value[k]) != enc(SAMPLING[k]) for k in value):` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 460 | + | `            refuse('scheduled_sampling permits only force_from_step=1 and max_own_probability=0.5')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 461 | + | `    if set(oc.get('recipe', {}))-{'milestones', 'scheduled_sampling'}: refuse('unknown recipe keys')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 462 | + | `    if 'milestones' in oc.get('recipe', {}) and oc['recipe']['milestones'] != [100, 200]: refuse('recipe milestones differ')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 463 | + | `    if 'code_tree' in over:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 464 | + | `        if '4.json' not in over.get('add_k', {}): refuse('code_tree requires add_k 4.json')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 465 | + | `        if new != {'h1', 'milestones', 'recipe', 'scheduled_sampling'} or oc['recipe'] != dict(milestones=[100, 200], scheduled_sampling=SAMPLING) or oc['scheduled_sampling'] != SAMPLING:` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 466 | + | `            refuse('code_tree requires the complete registered settings')` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 467 | + | `` | Restrict new settings to the registered H1 block and the two declared sampling deltas; preserve every other recipe field. |
| H1 468 | + | `def code_records(code):` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 469 | + | `    return {'k/7.json', 'k/s1_record.json', 'k/archive.json', 'k/' + Path(code['archive']['path']).name,` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 470 | + | `            'b/c.sh', 'b/p0.sh', 'b/r.sh', 'b/h.py', 'b/i.py', 'job.sh'}` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 471 | + | `` | Exempt only independently validated regenerated code records from the data-only placement comparison. |
| H1 472 | + | `def read_override_pin(value):` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 473 | + | `    if not isinstance(value, dict) or set(value) != {'path', 'sha256'} or not HEX64.fullmatch(str(value['sha256'])):` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 474 | + | `        refuse('malformed code override pin')` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 475 | + | `    if sha(value['path']) != value['sha256']: refuse('code override pin differs')` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 476 | + | `    return Path(value['path'])` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 477 | + | `` | Require an exact file/SHA256 pin before reading code or archive evidence. |
| H1 478 | + | `def replace_once(fs, path, before, after):` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 479 | + | `    text = path.read_text()` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 480 | + | `    if text.count(before) != 1: refuse('fixed runtime patch does not match ' + path.name)` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 481 | + | `    fs.text(path, text.replace(before, after))` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 482 | + | `` | Apply each fixed runtime patch only when the sealed source matches exactly. |
| H1 483 | + | `def install_code(kit, out, over, cfg, cur, launch, fs):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 484 | + | `    if over['run_key'] != '17c4ffa4': refuse('unregistered run')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 485 | + | `    value = over['code_tree']` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 486 | + | `    if not isinstance(value, dict) or set(value)-{'archive', 'pin', 'archive_record'} or not {'archive', 'pin'} <= set(value):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 487 | + | `        refuse('unknown or incomplete code_tree keys')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 488 | + | `    archive = read_override_pin(value['archive']); pin = read_override_pin(value['pin'])` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 489 | + | `    code = json.loads(pin.read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 490 | + | `    if set(code) != {'schema', 'commit', 'tree_sha256', 'files', 'sources', 'operation_sources', 'archive'} or code['schema'] != 'c1-sealed-source-v1':` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 491 | + | `        refuse('code pin schema differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 492 | + | `    tree = digest(code['files']); name = 't_' + tree[:16] + '.tar'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 493 | + | `    if code['tree_sha256'] != tree or code['commit'] != 'sha256:' + tree or code['archive'] != dict(path=KIT_LOGICAL + name, sha256=sha(archive)):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 494 | + | `        refuse('code tree/archive identity differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 495 | + | `    members = {}; order = []` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 496 | + | `    with tarfile.open(archive) as tf:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 497 | + | `        for m in tf:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 498 | + | `            if not m.isfile() or not safe_rel(m.name) or m.name in members or m.size > 16_000_000 or (m.uid,m.gid,m.uname,m.gname,m.mtime) != (0,0,'','',0) or m.mode not in (0o644,0o755):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 499 | + | `                refuse('unsafe or nondeterministic source member')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 500 | + | `            order.append(m.name); members[m.name] = hashlib.sha256(tf.extractfile(m).read()).hexdigest()` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 501 | + | `    if order != sorted(order) or members != code['files']: refuse('archive members differ from code pin')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 502 | + | `    for key in ('sources', 'operation_sources'):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 503 | + | `        if not code[key] or any(members.get(n) != h for n,h in code[key].items()): refuse('source closure differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 504 | + | `    if members.get('auth/R0_ROOMS.txt') != H1['r0_rooms']['sha256']: refuse('required member is not sealed in tree')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 505 | + | `    fs.copy(archive, out / 'k' / name); fs.copy(pin, out / 'k/7.json')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 506 | + | `    record = json.loads((kit / 'k/s1_record.json').read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 507 | + | `    record['trees']['trainer'] = dict(commit=code['commit'], file_count=len(members), files=members)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 508 | + | `    fs.write(out / 'k/s1_record.json', record)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 509 | + | `    cur['record'] = dict(file=KIT_LOGICAL + 's1_record.json', sha256=sha(out / 'k/s1_record.json'))` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 510 | + | `    cur['trainer'] = dict(file=code['archive']['path'], sha256=code['archive']['sha256'])` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 511 | + | `    cur['commit'] = code['commit']; cfg['code'] = dict(path=KIT_LOGICAL + '7.json', sha256=sha(out / 'k/7.json'))` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 512 | + | `    launch['source_revision'] = code['commit']; launch['slot']['wall_seconds'] = 46800` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 513 | + | `    if 'archive_record' in value:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 514 | + | `        rec = json.loads(read_override_pin(value['archive_record']).read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 515 | + | `        location = str(archive)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 516 | + | `        if not PART.fullmatch(location): refuse('archive attestation must name the uploaded project archive')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 517 | + | `        if rec.get('status') != 'ARCHIVED' or rec.get('durable') is not True or rec.get('location') != location or rec.get('sha256') != sha(archive) or rec.get('tree_sha256') != tree or rec.get('bytes') != archive.stat().st_size:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 518 | + | `            refuse('archive attestation differs')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 519 | + | `    else:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 520 | + | `        if over.get('status') == 'READY': refuse('READY needs an off-scratch archive attestation')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 521 | + | `        rec = dict(schema='s1-source-archive-v1', status='PENDING', durable=False,` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 522 | + | `                   sha256=sha(archive), tree_sha256=tree, bytes=archive.stat().st_size)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 523 | + | `    fs.write(out / 'k/archive.json', rec)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 524 | + | `    if '4.json' in over.get('add_k', {}):` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 525 | + | `        auth = json.loads((out / 'k/4.json').read_text())` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 526 | + | `        if auth.get('source_revision') != code['commit'] or auth.get('config_sha256') != identity(cfg) or auth.get('production_go_granted') is not False or auth.get('wall_seconds') != 46800:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 527 | + | `            refuse('new source needs its own conditional authorization')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 528 | + | `    # Both paths refer to the same inode through c.sh's NR -> X/runs writable bind.` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 529 | + | `    replace_once(fs, out / 'b/r.sh', '    printf \'USR1\\n\' >> "$stop_file"',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 530 | + | `        '    printf \'USR1\\n\' >> "$stop_file"\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 531 | + | `        '    run_dir=$(/usr/bin/python3 -I -c \'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])\' "$HX/k/launch.json")\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 532 | + | `        '    mkdir -p "$run_dir"\n'` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 533 | + | `        '    printf \'USR1\\n\' >> "$run_dir/stop.${SLURM_JOB_ID:-local}.request"')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 534 | + | `    replace_once(fs, out / 'b/h.py', 'except (FileNotFoundError, ProcessLookupError):',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 535 | + | `                 'except (FileNotFoundError, ProcessLookupError, PermissionError):')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 536 | + | `    replace_once(fs, out / 'b/i.py', '        except FileNotFoundError: pass',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 537 | + | `                 '        except (FileNotFoundError, PermissionError): pass')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 538 | + | `    replace_once(fs, out / 'job.sh', '#SBATCH --time=24:00:00', '#SBATCH --time=13:00:00')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 539 | + | `    for before, after in [` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 540 | + | `        ('S=/tmp/jjyeung/okit_$K/root', 'S=/tmp/jjyeung/a_17c4ffa4/root'),` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 541 | + | `        ('NX=/tmp/jjyeung/okit_$K/x_${SLURM_JOB_ID:-local}', 'NX=/tmp/jjyeung/a_17c4ffa4/x_${SLURM_JOB_ID:-local}'),` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 542 | + | `        ('NR=${TK_RUNS_DIR:-/tmp/jjyeung/okit_$K/runs}', 'NR=/tmp/jjyeung/a_17c4ffa4/runs')]:` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 543 | + | `        replace_once(fs, out / 'b/c.sh', before, after)` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 544 | + | `    replace_once(fs, out / 'b/p0.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.preflight',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 545 | + | `                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.preflight')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 546 | + | `    replace_once(fs, out / 'b/r.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.${1:-x}',` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 547 | + | `                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.${1:-x}')` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 548 | + | `` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| H1 549 | + | `` | Validate archive members and code closure; regenerate source bindings, conditional authorization and the fixed stop bridge. |
| D0 357 | − | `    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the data-only set ' + str(sorted(set(over['config']) - CONFIG)))` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 553 | + | `    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the admitted set ' + str(sorted(set(over['config']) - CONFIG)))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 560 | + | `    validate_h1(over)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 566 | + | `    if sha(kit / 'SHA256SUMS.txt') != SEALED_MANIFEST: refuse('the source is not the sealed kit 07ca49df (derive from the sealed kit only)')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 567 | + | `    members = manifest_members(kit)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 568 | + | `    for name in sorted(member_directories(members), key=lambda n: (len(Path(n).parts), n)):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 569 | + | `        if not stat.S_ISDIR((kit / name).lstat().st_mode): refuse('unsupported source directory')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 373 | − | `        if not p.is_file(): missing.append(name); continue` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 574 | + | `        try: mode = p.lstat().st_mode` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 575 | + | `        except FileNotFoundError: missing.append(name); continue` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 576 | + | `        if not stat.S_ISREG(mode): refuse('unsupported source member')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 385 | − | `    changing = bool(over.get('config') or over.get('deployment') or over.get('add_k')` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 588 | + | `    changing = bool(over.get('code_tree') or over.get('config') or over.get('deployment') or over.get('add_k')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 613 | + | `    for name in ('h1', 'milestones'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 614 | + | `        if name in oc: cfg[name] = copy.deepcopy(oc[name])` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 615 | + | `    for name in ('scheduled_sampling', 'recipe'):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 616 | + | `        if name in oc:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 617 | + | `            cfg[name] = copy.deepcopy(cfg[name])` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 618 | + | `            for k, v in oc[name].items():` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 619 | + | `                if name == 'recipe' and k == 'scheduled_sampling':` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 620 | + | `                    cfg[name][k] = {**cfg[name][k], **v}` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 621 | + | `                else: cfg[name][k] = copy.deepcopy(v)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 412 | − | `    out.mkdir()` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 413 | − | `    shutil.copytree(kit / 'b', out / 'b')` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 414 | − | `    for name in ('job.sh', 'job8.sh'): shutil.copy2(kit / name, out / name)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 415 | − | `    (out / 'k').mkdir(); (out / 'o').mkdir(); (out / 'runs').mkdir()` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 416 | − | `    for p in sorted((kit / 'k').iterdir()):` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 417 | − | `        if p.name in ('launch.json', '1.json', '0.json', old_key + '.json'): continue` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 418 | − | `        shutil.copy2(p, out / 'k' / p.name)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 624 | + | `    out.mkdir(mode=0o700)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 625 | + | `    fs = SealedOutput(out, stat.S_IMODE((kit / 'k/1.json').stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 626 | + | `    if 'code_tree' in over and (out.stat().st_mode & 0o777) != 0o700: refuse('directory mode differs')` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 627 | + | `    for name in sorted(member_directories(members) - {'.'}, key=lambda n: (len(Path(n).parts), n)):` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 628 | + | `        fs.mkdir(out / name, stat.S_IMODE((kit / name).stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 629 | + | `    for name in members:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 630 | + | `        if name in missing or (changing and name == 'k/' + old_key + '.json'): continue` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 631 | + | `        fs.copy(kit / name, out / name, stat.S_IMODE((kit / name).stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 632 | + | `    if changing:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 633 | + | `        for name in ('o', 'runs'): fs.mkdir(out / name, 0o700)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 421 | − | `        shutil.copyfile(pin['path'], out / 'k' / name)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 636 | + | `        fs.copy(pin['path'], out / 'k' / name)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 639 | + | `` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 640 | + | `    if 'code_tree' in over:` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 641 | + | `        install_code(kit, out, over, cfg, cur, launch, fs)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 435 | − | `        if (kit / 'k' / name).exists(): refuse('add_k may not overwrite the sealed k/' + name)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 653 | + | `        if 'k/' + name in src_inventory: refuse('add_k may not overwrite the sealed k/' + name)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 445 | − | `    write(out / 'k' / (key + '.json'), cfg)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 446 | − | `    write(out / 'k/1.json', {'0': key})` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 447 | − | `    write(out / 'k/0.json', cur)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 448 | − | `    code = json.loads((kit / 'k/7.json').read_text())` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 663 | + | `    fs.write(out / 'k' / (key + '.json'), cfg, stat.S_IMODE((kit / 'k' / (old_key + '.json')).stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 664 | + | `    fs.write(out / 'k/1.json', {'0': key})` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 665 | + | `    fs.write(out / 'k/0.json', cur)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 666 | + | `    code = json.loads((out / 'k/7.json').read_text())` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 452 | − | `                  run_directory=f'/tmp/jjyeung/okit_8865619b/runs/{run}', source_seal={**seal, 'sha256': digest(seal)},` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 670 | + | `                  run_directory=(f'/tmp/jjyeung/a_{run}/runs/{run}' if 'code_tree' in over else f'/tmp/jjyeung/okit_8865619b/runs/{run}'), source_seal={**seal, 'sha256': digest(seal)},` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 479 | − | `    write(out / 'k/launch.json', launch)` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 697 | + | `    fs.write(out / 'k/launch.json', launch)` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| D0 483 | − | `    (out / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(inventory.items())))` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 484 | − | `    if changing:  # explicit placeholder: a.py refuses until an independent content scan replaces it` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| D0 485 | − | `        write(out / 'ANON_OK.json', dict(status='UNREVIEWED', hits=None, manifest_sha256=sha(out / 'SHA256SUMS.txt'), external=[],` | Replace this line with the bounded extension shown below; retain the remaining sealed behavior. |
| H1 701 | + | `    fs.text(out / 'SHA256SUMS.txt', ''.join(f'{v}  {k}\n' for k, v in sorted(inventory.items())), stat.S_IMODE((kit / 'SHA256SUMS.txt').stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 702 | + | `    # Never inherit an unmanifested certificate; require independent content review.` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 703 | + | `    fs.write(out / 'ANON_OK.json', dict(status='UNREVIEWED', hits=None, manifest_sha256=sha(out / 'SHA256SUMS.txt'), external=[],` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |
| H1 705 | + | `    if not changing: out.chmod(stat.S_IMODE(kit.stat().st_mode))` | Apply the bounded additions and bind the resulting config, source seal and launch identity. |

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

Tests: `evidence/derivation.json`, `evidence/archive_layout.json`, `evidence/stop_bridge/result.json`, `evidence/gate_binding.json`, `evidence/staging_test/result.json`, and `evidence/cpu/fallback_fix5/result.json`. The fixed four-rank chain is prepared in tests/RERUN_CHAIN.sh and has only been syntax-checked; it awaits the operator run outside the socket-restricted sandbox. The step-200 fallback uses a native tiny model and real checkpoint/export serialization with local one-rank collective stand-ins.

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
@@ -123,4 +123,45 @@
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
+# Source membership, copying and dependency reads share the sealed manifest boundary.
+s=s.replace("    missing, src_inventory = [], {}", """    if sha(kit / 'SHA256SUMS.txt') != SEALED_MANIFEST: refuse('the source is not the sealed kit 07ca49df (derive from the sealed kit only)')
+    members = manifest_members(kit)
+    for name in sorted(member_directories(members), key=lambda n: (len(Path(n).parts), n)):
+        if not stat.S_ISDIR((kit / name).lstat().st_mode): refuse('unsupported source directory')
+    missing, src_inventory = [], {}""")
+s=s.replace("        if not p.is_file(): missing.append(name); continue", """        try: mode = p.lstat().st_mode
+        except FileNotFoundError: missing.append(name); continue
+        if not stat.S_ISREG(mode): refuse('unsupported source member')""")
+start = s.index('    out.mkdir(mode=0o700)')
+end = s.index("    for name, pin in over.get('add_k', {}).items():", start)
+s = s[:start] + """    out.mkdir(mode=0o700)
+    fs = SealedOutput(out, stat.S_IMODE((kit / 'k/1.json').stat().st_mode))
+    if 'code_tree' in over and (out.stat().st_mode & 0o777) != 0o700: refuse('directory mode differs')
+    for name in sorted(member_directories(members) - {'.'}, key=lambda n: (len(Path(n).parts), n)):
+        fs.mkdir(out / name, stat.S_IMODE((kit / name).stat().st_mode))
+    for name in members:
+        if name in missing or (changing and name == 'k/' + old_key + '.json'): continue
+        fs.copy(kit / name, out / name, stat.S_IMODE((kit / name).stat().st_mode))
+    if changing:
+        for name in ('o', 'runs'): fs.mkdir(out / name, 0o700)
+""" + s[end:]
+s=s.replace("[json.loads(p.read_text()) for p in sorted((kit / 'k').iterdir()) if p.suffix == '.json' and p.is_file()]",
+            "[json.loads((kit / n).read_text()) for n in manifest_members(kit) if n.startswith('k/') and n.endswith('.json') and n not in missing]")
+s=s.replace("if (kit / 'k' / name).exists():", "if 'k/' + name in src_inventory:")
+s=s.replace("fs.write(out / 'k' / (key + '.json'), cfg)", "fs.write(out / 'k' / (key + '.json'), cfg, stat.S_IMODE((kit / 'k' / (old_key + '.json')).stat().st_mode))")
+s=s.replace("    (out / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\\n' for k, v in sorted(inventory.items())))", "    fs.text(out / 'SHA256SUMS.txt', ''.join(f'{v}  {k}\\n' for k, v in sorted(inventory.items())), stat.S_IMODE((kit / 'SHA256SUMS.txt').stat().st_mode))")
+s=s.replace("    if changing:  # explicit placeholder: a.py refuses until an independent content scan replaces it\n        fs.write(out / 'ANON_OK.json',", "    # Never inherit an unmanifested certificate; require independent content review.\n    fs.write(out / 'ANON_OK.json',")
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
+ # Reproduce sealed members with empty overrides; exclude all source runtime state.
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
@@ -73,19 +75,20 @@
  private(KH)
  assert r['config_identity']==ids['identity'], 'configuration identity differs'
  w(B/'result.json',r)
- # Compare the complete final inventory to a complete temporary derivation, not a FIXTURE launch hash.
+ # Compare the complete sealed inventory to a temporary derivation, not a FIXTURE launch hash.
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
@@ -0,0 +1,83 @@
+"""Mode-preserving writes confined to one derived output tree."""
+from contextlib import contextmanager
+import stat
+from pathlib import Path
+
+
+def manifest_members(root):
+    """Read the sealed member names without walking the surrounding runtime tree."""
+    names = []
+    for line in (Path(root) / 'SHA256SUMS.txt').read_text().splitlines():
+        digest_, name = line.split('  ', 1)
+        if (len(digest_) != 64 or any(c not in '0123456789abcdef' for c in digest_)
+                or name.startswith('/') or any(p in ('', '.', '..') for p in name.split('/'))
+                or name in names):
+            raise ValueError('invalid sealed member')
+        names.append(name)
+    return sorted(names)
+
+
+def member_directories(names):
+    return {'.'} | {str(p) for name in names for p in Path(name).parents}
+
+
+def mode_inventory(root):
+    root = Path(root)
+    names = manifest_members(root)
+    dirs = member_directories(names)
+    modes = {}
+    for name in sorted(set(names) | dirs, key=lambda n: (len(Path(n).parts), n)):
+        mode = (root / name).lstat().st_mode
+        if not (stat.S_ISDIR(mode) if name in dirs else stat.S_ISREG(mode)):
+            raise ValueError('unsupported sealed member: ' + name)
+        modes[name] = stat.S_IMODE(mode)
+    return modes
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
@@ -0,0 +1,157 @@
+"""Exercise full derivation with sealed permissions, using only local CPU fixtures."""
+import copy, hashlib, importlib.util, json, os, shutil, stat, sys, subprocess
+from pathlib import Path
+
+H = Path(__file__).resolve().parents[1]
+D = Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0')
+sys.path.insert(0, str(H / 'tools'))
+import derive_kit_h1 as dk
+
+root = H / 'evidence/fix4_sealed_modes'
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
+    before = {n: v for n, v in before.items() if n in dk.mode_inventory(kit)}
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
+            assert {n: actual[n] for n in dk.mode_inventory(out)} == {n: before[n] for n in dk.mode_inventory(kit)}
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
+(H / 'evidence/fix4_sealed_modes.json').write_text(json.dumps(result, indent=2) + '\n')
+print(json.dumps(result, indent=2))
```

Manifest membership bounds source validation, copies, dependency-record reads and mode comparisons. Changed outputs create fresh empty runtime directories; every output receives an UNREVIEWED certificate without reading the unmanifested source certificate. REVIEW4.md covers the real SRC/E/P listings and each login entrypoint. The exact-listing fixture includes all 90 runtime entries and reproduces the fix-3 comparison failure.

```diff
--- fix3/tools/sealed_output.py
+++ current/tools/sealed_output.py
@@ -4,10 +4,34 @@
 from pathlib import Path
 
 
+def manifest_members(root):
+    """Read the sealed member names without walking the surrounding runtime tree."""
+    names = []
+    for line in (Path(root) / 'SHA256SUMS.txt').read_text().splitlines():
+        digest_, name = line.split('  ', 1)
+        if (len(digest_) != 64 or any(c not in '0123456789abcdef' for c in digest_)
+                or name.startswith('/') or any(p in ('', '.', '..') for p in name.split('/'))
+                or name in names):
+            raise ValueError('invalid sealed member')
+        names.append(name)
+    return sorted(names)
+
+
+def member_directories(names):
+    return {'.'} | {str(p) for name in names for p in Path(name).parents}
+
+
 def mode_inventory(root):
     root = Path(root)
-    return {str(p.relative_to(root)): stat.S_IMODE(p.stat().st_mode)
-            for p in [root, *sorted(root.rglob('*'))]}
+    names = manifest_members(root)
+    dirs = member_directories(names)
+    modes = {}
+    for name in sorted(set(names) | dirs, key=lambda n: (len(Path(n).parts), n)):
+        mode = (root / name).lstat().st_mode
+        if not (stat.S_ISDIR(mode) if name in dirs else stat.S_ISREG(mode)):
+            raise ValueError('unsupported sealed member: ' + name)
+        modes[name] = stat.S_IMODE(mode)
+    return modes
 
 
 class SealedOutput:
```

```diff
--- fix3/tools/make_deriver.py
+++ current/tools/make_deriver.py
@@ -135,19 +135,33 @@
 s=s.replace('shutil.copyfile(pin, out /', 'fs.copy(pin, out /')
 s=s.replace("shutil.copyfile(pin['path'], out /", "fs.copy(pin['path'], out /")
 s=s.replace('write(out /', 'fs.write(out /')
-s=s.replace("    out.mkdir(mode=0o700)", """    # Copy only regular files/directories; never follow a sealed link into another tree.
-    for p in kit.rglob('*'):
-        if p.is_symlink() or not (p.is_file() or p.is_dir()): refuse('unsupported source member')
-    out.mkdir(mode=0o700)
-    fs = SealedOutput(out, stat.S_IMODE((kit / 'k/1.json').stat().st_mode))""")
-s=s.replace("    (out / 'k').mkdir(); (out / 'o').mkdir(); (out / 'runs').mkdir()", """    for name in ('k', 'o', 'runs'):
-        if not changing and not (kit / name).exists(): continue
-        mode = stat.S_IMODE((kit / name).stat().st_mode) if (kit / name).exists() else 0o700
-        fs.mkdir(out / name, mode)""")
-s=s.replace("        if p.name in ('launch.json', '1.json', '0.json', old_key + '.json'): continue\n        shutil.copy2(p, out / 'k' / p.name)", """        if p.name == old_key + '.json' and changing: continue
-        fs.copy(p, out / 'k' / p.name, stat.S_IMODE(p.stat().st_mode))""")
+# Source membership, copying and dependency reads share the sealed manifest boundary.
+s=s.replace("    missing, src_inventory = [], {}", """    if sha(kit / 'SHA256SUMS.txt') != SEALED_MANIFEST: refuse('the source is not the sealed kit 07ca49df (derive from the sealed kit only)')
+    members = manifest_members(kit)
+    for name in sorted(member_directories(members), key=lambda n: (len(Path(n).parts), n)):
+        if not stat.S_ISDIR((kit / name).lstat().st_mode): refuse('unsupported source directory')
+    missing, src_inventory = [], {}""")
+s=s.replace("        if not p.is_file(): missing.append(name); continue", """        try: mode = p.lstat().st_mode
+        except FileNotFoundError: missing.append(name); continue
+        if not stat.S_ISREG(mode): refuse('unsupported source member')""")
+start = s.index('    out.mkdir(mode=0o700)')
+end = s.index("    for name, pin in over.get('add_k', {}).items():", start)
+s = s[:start] + """    out.mkdir(mode=0o700)
+    fs = SealedOutput(out, stat.S_IMODE((kit / 'k/1.json').stat().st_mode))
+    if 'code_tree' in over and (out.stat().st_mode & 0o777) != 0o700: refuse('directory mode differs')
+    for name in sorted(member_directories(members) - {'.'}, key=lambda n: (len(Path(n).parts), n)):
+        fs.mkdir(out / name, stat.S_IMODE((kit / name).stat().st_mode))
+    for name in members:
+        if name in missing or (changing and name == 'k/' + old_key + '.json'): continue
+        fs.copy(kit / name, out / name, stat.S_IMODE((kit / name).stat().st_mode))
+    if changing:
+        for name in ('o', 'runs'): fs.mkdir(out / name, 0o700)
+""" + s[end:]
+s=s.replace("[json.loads(p.read_text()) for p in sorted((kit / 'k').iterdir()) if p.suffix == '.json' and p.is_file()]",
+            "[json.loads((kit / n).read_text()) for n in manifest_members(kit) if n.startswith('k/') and n.endswith('.json') and n not in missing]")
+s=s.replace("if (kit / 'k' / name).exists():", "if 'k/' + name in src_inventory:")
 s=s.replace("fs.write(out / 'k' / (key + '.json'), cfg)", "fs.write(out / 'k' / (key + '.json'), cfg, stat.S_IMODE((kit / 'k' / (old_key + '.json')).stat().st_mode))")
 s=s.replace("    (out / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\\n' for k, v in sorted(inventory.items())))", "    fs.text(out / 'SHA256SUMS.txt', ''.join(f'{v}  {k}\\n' for k, v in sorted(inventory.items())), stat.S_IMODE((kit / 'SHA256SUMS.txt').stat().st_mode))")
-s=s.replace("    if changing:  # explicit placeholder", "    if (kit / 'ANON_OK.json').is_file():\n        fs.copy(kit / 'ANON_OK.json', out / 'ANON_OK.json', stat.S_IMODE((kit / 'ANON_OK.json').stat().st_mode))\n    if changing:  # explicit placeholder")
+s=s.replace("    if changing:  # explicit placeholder: a.py refuses until an independent content scan replaces it\n        fs.write(out / 'ANON_OK.json',", "    # Never inherit an unmanifested certificate; require independent content review.\n    fs.write(out / 'ANON_OK.json',")
 s=s.replace('    return dict(config_key=key,', "    if not changing: out.chmod(stat.S_IMODE(kit.stat().st_mode))\n    return dict(config_key=key,")
 Path('tools/derive_kit_h1.py').write_text(s)
```

```diff
--- fix3/tools/orchard_records.py
+++ current/tools/orchard_records.py
@@ -48,7 +48,7 @@
  sys.path.insert(0,str(B/'p/b'));from d import contract
  la=load(B/'p/k/launch.json');cfg=load(B/'p'/la['config']['file'])
  assert result['config_identity']==ids['identity'] and dk.digest(contract(la,cfg))==ids['contract']
- # Reproduce the complete source kit with empty overrides, including member modes.
+ # Reproduce sealed members with empty overrides; exclude all source runtime state.
  dk.derive(base,B/'e',{})
  assert manifest(B/'e')==manifest(base)
  for n,h in manifest(base).items():assert dk.sha(B/'e'/n)==h
@@ -75,7 +75,7 @@
  private(KH)
  assert r['config_identity']==ids['identity'], 'configuration identity differs'
  w(B/'result.json',r)
- # Compare the complete final inventory to a complete temporary derivation, not a FIXTURE launch hash.
+ # Compare the complete sealed inventory to a temporary derivation, not a FIXTURE launch hash.
  candidate=B/'q';test=dict(o,fixture=True,status='BLOCKED');dk.derive(base,candidate,test)
  la=load(candidate/'k/launch.json');la.update(status='READY',production_authorized=True);dk.SealedOutput(candidate).write(candidate/'k/launch.json',la)
  man=manifest(candidate);man['k/launch.json']=dk.sha(candidate/'k/launch.json')
```

```diff
--- fix3/tests/test_runtime_inventory.py
+++ current/tests/test_runtime_inventory.py
@@ -0,0 +1,177 @@
+"""Reproduce the real Orchard listing; keep every operation local and CPU-only."""
+import hashlib, importlib.util, json, os, runpy, stat, subprocess, sys
+from pathlib import Path
+from unittest.mock import patch
+
+H = Path(__file__).resolve().parents[1]
+D = Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0/kitfull')
+sys.path.insert(0, str(H / 'tools'))
+import derive_kit_h1 as dk
+
+root = H / 'evidence/fix4_listing'
+root.mkdir(mode=0o700)
+listing = (H / 'evidence_orchard_q7_2157Z.txt').read_text()
+sections = {}
+for line in listing.splitlines():
+    if line.startswith('### '):
+        section = line[4:]; sections[section] = {}
+    elif section != 'SRC sizes' and line.strip():
+        mode, kind, name = line.split(' ', 2)
+        sections[section][name or '.'] = (int(mode, 8), kind)
+src, empty, provisional = (sections[n] for n in ('SRC x_07ca49df', 'E', 'P'))
+runtime = set(src) - set(empty)
+assert len(src) == 193 and len(empty) == 103 and len(runtime) == 90
+assert not runtime & set(provisional)
+assert all(src[n] == empty[n] for n in set(src) & set(empty))
+
+base = root / 'x_07ca49df'
+base.mkdir(mode=0o700)
+members = dk.manifest_members(D)
+synthetic = []
+# Retain required sealed JSON and executable bytes; unavailable payloads and runtime
+# files use small stand-ins. No real runtime-state content is available or opened.
+for name, (mode, kind) in sorted(src.items(), key=lambda row: (len(Path(row[0]).parts), row[0])):
+    if name == '.': continue
+    p = base / name
+    if kind == 'd': p.mkdir(mode=0o700)
+    else:
+        assert kind == 'f'
+        if name in members and (D / name).is_file(): p.write_bytes((D / name).read_bytes())
+        else:
+            p.write_bytes(b'local listing fixture\n')
+            if name in members: synthetic.append(name)
+(base / 'SHA256SUMS.txt').write_text(''.join(dk.sha(base / n) + '  ' + n + '\n' for n in members))
+for name, (mode, kind) in sorted(src.items(), key=lambda row: -len(Path(row[0]).parts)):
+    (base / name).chmod(mode)
+pin = dk.sha(base / 'SHA256SUMS.txt')
+dk.SEALED_MANIFEST = pin
+assert len(synthetic) == 2
+
+def metadata(tree):
+    return {str(p.relative_to(tree)): (stat.S_IMODE(p.lstat().st_mode),
+            'd' if p.is_dir() else 'f') for p in [tree, *tree.rglob('*')]}
+
+assert metadata(base) == src
+before_modes = metadata(base)
+before_sealed = {n: dk.sha(base / n) for n in members}
+ids = json.loads((H / 'ids.json').read_text())
+over = json.loads((H / 'build/over_local.json').read_text())
+over.pop('fixture', None)
+result = dict(source_entries=len(src), runtime_entries=len(runtime),
+              runtime_names=sorted(runtime), synthetic_payloads=synthetic,
+              listing_sha256=dk.sha(H / 'evidence_orchard_q7_2157Z.txt'))
+
+def bundle(name, prior=False):
+    b = root / name; b.mkdir(mode=0o700)
+    tree = H / 'evidence/fix4_before' if prior else H
+    source = (tree / 'tools/derive_kit_h1.py').read_text().replace(
+        "SEALED_MANIFEST = 'de6e7e0fac4036889fb4112792fbaa2d6f362a0cde09722ba6e93a6a39e7f32b'",
+        'SEALED_MANIFEST = ' + repr(pin))
+    (b / 'd.py').write_text(source)
+    (b / 'r.py').write_text((tree / 'tools/orchard_records.py').read_text().replace(
+        "O=Path('/project/community/jjyeung/okh7')", 'O=Path(' + repr(str(root)) + ')'))
+    (b / 'ids.json').write_text(json.dumps(ids))
+    (b / 'over.json').write_text(json.dumps(over))
+    return b
+
+old = bundle('old', prior=True)
+rc = subprocess.run([sys.executable, '-B', str(old / 'r.py'), 'prepare'], capture_output=True, text=True)
+assert rc.returncode != 0 and 'member modes differ' in rc.stderr, rc.stderr
+assert (old / 'p.json').is_file() and (old / 'e/SHA256SUMS.txt').is_file()
+(root / 'fix3_failure.log').write_text(rc.stdout + rc.stderr)
+result['fix3_prepare'] = 'EXPECTED FAILURE: member modes differ'
+
+# Deny source access outside the manifest boundary, including recursive listing.
+# This also prevents accidental reads/copies of the unmanifested certificate.
+allowed = set(members) | dk.member_directories(members) | {'SHA256SUMS.txt'}
+original_open, original_stat, original_iterdir = Path.open, Path.stat, Path.iterdir
+def guard(p):
+    try: name = str(p.relative_to(base))
+    except ValueError: return
+    assert name in allowed, 'unlisted source access: ' + name
+def guarded_open(p, *a, **kw):
+    guard(p); return original_open(p, *a, **kw)
+def guarded_stat(p, *a, **kw):
+    guard(p); return original_stat(p, *a, **kw)
+def guarded_iterdir(p):
+    assert p != base and base not in p.parents, 'source traversal: ' + str(p)
+    return original_iterdir(p)
+
+new = bundle('new')
+with patch.object(Path, 'open', guarded_open), patch.object(Path, 'stat', guarded_stat), \
+        patch.object(Path, 'iterdir', guarded_iterdir), patch.object(sys, 'argv', [str(new / 'r.py'), 'prepare']):
+    runpy.run_path(str(new / 'r.py'), run_name='__main__')
+assert json.loads((new / 'e.json').read_text())['status'] == 'PASS'
+assert (new / 'e/SHA256SUMS.txt').read_bytes() == (base / 'SHA256SUMS.txt').read_bytes()
+assert dk.mode_inventory(new / 'e') == dk.mode_inventory(base)
+assert set(dk.mode_inventory(base)) == set(members) | dk.member_directories(members)
+for out in (new / 'p', new / 'e'):
+    assert not runtime & set(metadata(out))
+    for n in dk.manifest_members(out):
+        want = dict(reversed(line.split('  ', 1)) for line in (out / 'SHA256SUMS.txt').read_text().splitlines())[n]
+        assert dk.sha(out / n) == want
+assert all(not list((new / 'p' / n).iterdir()) for n in ('o', 'runs'))
+assert json.loads((new / 'p/ANON_OK.json').read_text())['status'] == 'UNREVIEWED'
+result['prepare_and_empty_reproduction'] = 'PASS'
+result['source_access_guard'] = 'PASS'
+
+# Poison unlisted files under executable/record directories and add a dangling link.
+# They must neither be inspected nor enter the generated executable inventory.
+fs = dk.SealedOutput(base)
+fs.text(base / 'b/unlisted.py', 'raise RuntimeError("unlisted")\n')
+fs.text(base / 'k/unlisted.json', 'not JSON\n')
+(base / 'unlisted_link').symlink_to(root / 'absent')
+with patch.object(Path, 'open', guarded_open), patch.object(Path, 'stat', guarded_stat), \
+        patch.object(Path, 'iterdir', guarded_iterdir):
+    dk.derive(base, root / 'poison_empty', {})
+    dk.derive(base, root / 'poison_h1', over)
+for out in (root / 'poison_empty', root / 'poison_h1'):
+    assert not any((out / n).exists() for n in ('b/unlisted.py', 'k/unlisted.json', 'unlisted_link'))
+result['unlisted_files_and_link_ignored'] = 'PASS'
+
+# Execute the shipped final comparison against a candidate with real permissions.
+final = root / 'final'
+dk.derive(base, final, dict(over, fixture=True, status='BLOCKED'))
+la = json.loads((final / 'k/launch.json').read_text()); la.update(status='READY', production_authorized=True)
+dk.SealedOutput(final).write(final / 'k/launch.json', la)
+def manifest(tree):
+    return dict(reversed(line.split('  ', 1)) for line in (tree / 'SHA256SUMS.txt').read_text().splitlines())
+man = manifest(final); man['k/launch.json'] = dk.sha(final / 'k/launch.json')
+dk.SealedOutput(final).text(final / 'SHA256SUMS.txt', ''.join(h + '  ' + n + '\n' for n, h in sorted(man.items())))
+source = (H / 'payload/r.py').read_text()
+start = source.index(' # Compare the complete'); end = source.index(' # Separate ANON', start)
+block = '\n'.join(line[1:] for line in source[start:end].splitlines())
+scope = dict(B=new, o=over, dk=dk, base=base, KH=final, manifest=manifest,
+             load=lambda p: json.loads(p.read_text()))
+with patch.object(Path, 'open', guarded_open), patch.object(Path, 'stat', guarded_stat), \
+        patch.object(Path, 'iterdir', guarded_iterdir):
+    exec(block, scope)
+# Runtime mode changes do not affect comparison; member and ancestor changes do.
+(final / 'o/runtime').write_text('not a member\n'); (final / 'o').chmod(0o500)
+mode_line = next(line.strip() for line in block.splitlines() if 'assert dk.mode_inventory' in line)
+exec(mode_line, scope)
+for name in ('b/r.sh', 'b/sa', 'k/4.json', 'job.sh', '.'):
+    p = final / name; mode = stat.S_IMODE(p.stat().st_mode); p.chmod(mode ^ 0o200)
+    try:
+        try: exec(mode_line, scope)
+        except AssertionError: pass
+        else: raise AssertionError('member mode mismatch accepted: ' + name)
+    finally: p.chmod(mode)
+assert before_sealed == {n: dk.sha(base / n) for n in members}
+assert all(metadata(base)[n] == v for n, v in before_modes.items())
+result['final_comparison_and_mode_negatives'] = 'PASS'
+result['source_sealed_bytes_and_modes_unchanged'] = 'PASS'
+# Exercise the real certify entry and native exact-executable-inventory check.
+# This certificate is test data in the fixture, never an operator attestation.
+kh = root / ('x_' + ids['tokens']['kit']); final.rename(kh)
+cert_mode = stat.S_IMODE((kh / 'ANON_OK.json').stat().st_mode)
+(new / 'anon.json').write_text(json.dumps(dict(status='CLEAN', hits=0,
+    manifest_sha256=dk.sha(kh / 'SHA256SUMS.txt'), external=[])))
+rc = subprocess.run([sys.executable, '-B', str(new / 'r.py'), 'certify'], capture_output=True, text=True)
+assert rc.returncode == 0, rc.stderr
+assert stat.S_IMODE((kh / 'ANON_OK.json').stat().st_mode) == cert_mode
+assert json.loads((kh / 'ANON_OK.json').read_text())['status'] == 'CLEAN'
+result['certify_and_native_inventory_with_test_certificate'] = 'PASS'
+result['status'] = 'PASS'
+(H / 'evidence/fix4_listing.json').write_text(json.dumps(result, indent=2) + '\n')
+print(json.dumps(result, indent=2))
```
