from pathlib import Path
D=Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0')
s=(D/'tools/derive_kit.py').read_text()
s=s.replace('"""Derive a data-only kit', '"""Derive a data-only kit (or a narrowly admitted code-tree kit)')
s=s.replace('  config: {streams:', '  code_tree: {archive: {path, sha256}, pin: {path, sha256}, archive_record?: {path, sha256}}\n           validates deterministic source archive, regenerates tree bindings, installs fixed stop bridge;\n           archive_record is required for READY and must attest this archive off scratch.\n  config: {h1?, milestones?, recipe: {milestones?, scheduled_sampling?}?, scheduled_sampling?, streams:')
s=s.replace("import copy, hashlib, json, re, shutil, sys", "import copy, hashlib, json, re, shutil, sys, tarfile")
s=s.replace("'export_member_names', 'e00_listing'}", "'export_member_names', 'e00_listing', 'code_tree'}")
s=s.replace("CONFIG = {'streams', 'init_artifact', 's1_routing'}", "CONFIG = {'streams', 'init_artifact', 's1_routing', 'h1', 'milestones', 'recipe', 'scheduled_sampling'}")
s=s.replace("    out_man = {n: v for n, v in out_man.items() if n not in regen}", "    if 'code_tree' in over:\n        regen |= code_records(json.loads((out / 'k/7.json').read_text()))\n    out_man = {n: v for n, v in out_man.items() if n not in regen}")
s=s.replace("'config keys outside the data-only set '", "'config keys outside the admitted set '")
s=s.replace("    fixture = over.get('fixture') is True", "    validate_h1(over)\n    fixture = over.get('fixture') is True")
s=s.replace("changing = bool(over.get('config')", "changing = bool(over.get('code_tree') or over.get('config')")
s=s.replace("    for k, v in over.get('deployment', {}).items(): cur[k] = v", "    for name in ('h1', 'milestones'):\n        if name in oc: cfg[name] = copy.deepcopy(oc[name])\n    for name in ('scheduled_sampling', 'recipe'):\n        if name in oc:\n            cfg[name] = copy.deepcopy(cfg[name])\n            for k, v in oc[name].items():\n                if name == 'recipe' and k == 'scheduled_sampling':\n                    cfg[name][k] = {**cfg[name][k], **v}\n                else: cfg[name][k] = copy.deepcopy(v)\n    for k, v in over.get('deployment', {}).items(): cur[k] = v")
s=s.replace("    # Dependency chain: every changed config", "    if 'code_tree' in over:\n        install_code(kit, out, over, cfg, cur, launch)\n\n    # Dependency chain: every changed config")
s=s.replace("    code = json.loads((kit / 'k/7.json').read_text())", "    code = json.loads((out / 'k/7.json').read_text())")
helper=r'''
# Code changes have a separate validator; data staging never gains executable destinations.
H1 = dict(faithful_own_camera_rows=True, routing_pose_targets=True,
          camera_types=['camera_displacement', 'camera_movement_direction', 'camera_rotation'],
          stop_after_step=200, metrics=True,
          r0_rooms=dict(path='auth/R0_ROOMS.txt', sha256='bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3'))
SAMPLING = dict(force_from_step=1, max_own_probability=0.5)

def validate_h1(over):
    oc = over.get('config', {})
    new = set(oc) & {'h1', 'milestones', 'recipe', 'scheduled_sampling'}
    if new and 'code_tree' not in over: refuse('new training settings require code_tree')
    if 'h1' in oc and enc(oc['h1']) != enc(H1): refuse('only the registered h1 block is admitted')
    if 'milestones' in oc and enc(oc['milestones']) != enc([100, 200]): refuse('only milestones [100, 200] admitted')
    for value in [oc.get('scheduled_sampling', {}), oc.get('recipe', {}).get('scheduled_sampling', {})]:
        if not isinstance(value, dict) or set(value)-set(SAMPLING) or any(enc(value[k]) != enc(SAMPLING[k]) for k in value):
            refuse('scheduled_sampling permits only force_from_step=1 and max_own_probability=0.5')
    if set(oc.get('recipe', {}))-{'milestones', 'scheduled_sampling'}: refuse('unknown recipe keys')
    if 'milestones' in oc.get('recipe', {}) and oc['recipe']['milestones'] != [100, 200]: refuse('recipe milestones differ')
    if 'code_tree' in over:
        if '4.json' not in over.get('add_k', {}): refuse('code_tree requires add_k 4.json')
        if new != {'h1', 'milestones', 'recipe', 'scheduled_sampling'} or oc['recipe'] != dict(milestones=[100, 200], scheduled_sampling=SAMPLING) or oc['scheduled_sampling'] != SAMPLING:
            refuse('code_tree requires the complete registered settings')

def code_records(code):
    return {'k/7.json', 'k/s1_record.json', 'k/archive.json', 'k/' + Path(code['archive']['path']).name,
            'b/c.sh', 'b/p0.sh', 'b/r.sh', 'b/h.py', 'b/i.py', 'job.sh'}

def read_override_pin(value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'} or not HEX64.fullmatch(str(value['sha256'])):
        refuse('malformed code override pin')
    if sha(value['path']) != value['sha256']: refuse('code override pin differs')
    return Path(value['path'])

def replace_once(path, before, after):
    text = path.read_text()
    if text.count(before) != 1: refuse('fixed runtime patch does not match ' + path.name)
    path.write_text(text.replace(before, after))

def install_code(kit, out, over, cfg, cur, launch):
    if over['run_key'] != '17c4ffa4': refuse('unregistered run')
    value = over['code_tree']
    if not isinstance(value, dict) or set(value)-{'archive', 'pin', 'archive_record'} or not {'archive', 'pin'} <= set(value):
        refuse('unknown or incomplete code_tree keys')
    archive = read_override_pin(value['archive']); pin = read_override_pin(value['pin'])
    code = json.loads(pin.read_text())
    if set(code) != {'schema', 'commit', 'tree_sha256', 'files', 'sources', 'operation_sources', 'archive'} or code['schema'] != 'c1-sealed-source-v1':
        refuse('code pin schema differs')
    tree = digest(code['files']); name = 't_' + tree[:16] + '.tar'
    if code['tree_sha256'] != tree or code['commit'] != 'sha256:' + tree or code['archive'] != dict(path=KIT_LOGICAL + name, sha256=sha(archive)):
        refuse('code tree/archive identity differs')
    members = {}; order = []
    with tarfile.open(archive) as tf:
        for m in tf:
            if not m.isfile() or not safe_rel(m.name) or m.name in members or m.size > 16_000_000 or (m.uid,m.gid,m.uname,m.gname,m.mtime) != (0,0,'','',0) or m.mode not in (0o644,0o755):
                refuse('unsafe or nondeterministic source member')
            order.append(m.name); members[m.name] = hashlib.sha256(tf.extractfile(m).read()).hexdigest()
    if order != sorted(order) or members != code['files']: refuse('archive members differ from code pin')
    for key in ('sources', 'operation_sources'):
        if not code[key] or any(members.get(n) != h for n,h in code[key].items()): refuse('source closure differs')
    if members.get('auth/R0_ROOMS.txt') != H1['r0_rooms']['sha256']: refuse('R0 rooms not sealed in tree')
    shutil.copyfile(archive, out / 'k' / name); shutil.copyfile(pin, out / 'k/7.json')
    record = json.loads((kit / 'k/s1_record.json').read_text())
    record['trees']['trainer'] = dict(commit=code['commit'], file_count=len(members), files=members)
    write(out / 'k/s1_record.json', record)
    cur['record'] = dict(file=KIT_LOGICAL + 's1_record.json', sha256=sha(out / 'k/s1_record.json'))
    cur['trainer'] = dict(file=code['archive']['path'], sha256=code['archive']['sha256'])
    cur['commit'] = code['commit']; cfg['code'] = dict(path=KIT_LOGICAL + '7.json', sha256=sha(out / 'k/7.json'))
    launch['source_revision'] = code['commit']; launch['slot']['wall_seconds'] = 46800
    if 'archive_record' in value:
        rec = json.loads(read_override_pin(value['archive_record']).read_text())
        location = str(archive)
        if not PART.fullmatch(location): refuse('archive attestation must name the uploaded project archive')
        if rec.get('status') != 'ARCHIVED' or rec.get('durable') is not True or rec.get('location') != location or rec.get('sha256') != sha(archive) or rec.get('tree_sha256') != tree or rec.get('bytes') != archive.stat().st_size:
            refuse('archive attestation differs')
    else:
        if over.get('status') == 'READY': refuse('READY needs an off-scratch archive attestation')
        rec = dict(schema='s1-source-archive-v1', status='PENDING', durable=False,
                   sha256=sha(archive), tree_sha256=tree, bytes=archive.stat().st_size)
    write(out / 'k/archive.json', rec)
    if '4.json' in over.get('add_k', {}):
        auth = json.loads((out / 'k/4.json').read_text())
        if auth.get('source_revision') != code['commit'] or auth.get('config_sha256') != identity(cfg) or auth.get('production_go_granted') is not False or auth.get('wall_seconds') != 46800:
            refuse('new source needs its own conditional authorization')
    # Both paths refer to the same inode through c.sh's NR -> X/runs writable bind.
    replace_once(out / 'b/r.sh', '    printf \'USR1\\n\' >> "$stop_file"',
        '    printf \'USR1\\n\' >> "$stop_file"\n'
        '    run_dir=$(/usr/bin/python3 -I -c \'import json,sys; print(json.load(open(sys.argv[1]))["run_directory"])\' "$HX/k/launch.json")\n'
        '    mkdir -p "$run_dir"\n'
        '    printf \'USR1\\n\' >> "$run_dir/stop.${SLURM_JOB_ID:-local}.request"')
    replace_once(out / 'b/h.py', 'except (FileNotFoundError, ProcessLookupError):',
                 'except (FileNotFoundError, ProcessLookupError, PermissionError):')
    replace_once(out / 'b/i.py', '        except FileNotFoundError: pass',
                 '        except (FileNotFoundError, PermissionError): pass')
    replace_once(out / 'job.sh', '#SBATCH --time=24:00:00', '#SBATCH --time=13:00:00')
    for before, after in [
        ('S=/tmp/jjyeung/okit_$K/root', 'S=/tmp/jjyeung/a_17c4ffa4/root'),
        ('NX=/tmp/jjyeung/okit_$K/x_${SLURM_JOB_ID:-local}', 'NX=/tmp/jjyeung/a_17c4ffa4/x_${SLURM_JOB_ID:-local}'),
        ('NR=${TK_RUNS_DIR:-/tmp/jjyeung/okit_$K/runs}', 'NR=/tmp/jjyeung/a_17c4ffa4/runs')]:
        replace_once(out / 'b/c.sh', before, after)
    replace_once(out / 'b/p0.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.preflight',
                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.preflight')
    replace_once(out / 'b/r.sh', 'export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID:?}.${1:-x}',
                 'export TK_JOBDIR=/tmp/jjyeung/a_17c4ffa4/jobs/${SLURM_JOB_ID:?}.${1:-x}')

'''
s=s.replace('\ndef derive(kit, out, over):', '\n'+helper+'\ndef derive(kit, out, over):')
s=s.replace("    out.mkdir()", "    out.mkdir(mode=0o700)\n    if 'code_tree' in over and (out.stat().st_mode & 0o777) != 0o700: refuse('directory mode differs')")
s=s.replace("run_directory=f'/tmp/jjyeung/okit_8865619b/runs/{run}'", "run_directory=(f'/tmp/jjyeung/a_{run}/runs/{run}' if 'code_tree' in over else f'/tmp/jjyeung/okit_8865619b/runs/{run}')")
s=s.replace('only the registered h1 block is admitted', 'only the registered settings are admitted').replace('R0 rooms not sealed in tree', 'required member is not sealed in tree')
# Every mutation of the copied kit goes through an output-scoped writer.
mode_helpers = Path('tools/sealed_output.py').read_text()
s=s.replace('\ndef identity(cfg):', '\n' + mode_helpers + '\n\ndef identity(cfg):')
s=s.replace('def replace_once(path, before, after):', 'def replace_once(fs, path, before, after):')
s=s.replace('    path.write_text(text.replace(before, after))', '    fs.text(path, text.replace(before, after))')
s=s.replace('replace_once(out /', 'replace_once(fs, out /')
s=s.replace('def install_code(kit, out, over, cfg, cur, launch):', 'def install_code(kit, out, over, cfg, cur, launch, fs):')
s=s.replace('install_code(kit, out, over, cfg, cur, launch)', 'install_code(kit, out, over, cfg, cur, launch, fs)')
s=s.replace('shutil.copyfile(archive, out /', 'fs.copy(archive, out /')
s=s.replace('shutil.copyfile(pin, out /', 'fs.copy(pin, out /')
s=s.replace("shutil.copyfile(pin['path'], out /", "fs.copy(pin['path'], out /")
s=s.replace('write(out /', 'fs.write(out /')
# Source membership, copying and dependency reads share the sealed manifest boundary.
s=s.replace("    missing, src_inventory = [], {}", """    if sha(kit / 'SHA256SUMS.txt') != SEALED_MANIFEST: refuse('the source is not the sealed kit 07ca49df (derive from the sealed kit only)')
    members = manifest_members(kit)
    for name in sorted(member_directories(members), key=lambda n: (len(Path(n).parts), n)):
        if not stat.S_ISDIR((kit / name).lstat().st_mode): refuse('unsupported source directory')
    missing, src_inventory = [], {}""")
s=s.replace("        if not p.is_file(): missing.append(name); continue", """        try: mode = p.lstat().st_mode
        except FileNotFoundError: missing.append(name); continue
        if not stat.S_ISREG(mode): refuse('unsupported source member')""")
start = s.index('    out.mkdir(mode=0o700)')
end = s.index("    for name, pin in over.get('add_k', {}).items():", start)
s = s[:start] + """    out.mkdir(mode=0o700)
    fs = SealedOutput(out, stat.S_IMODE((kit / 'k/1.json').stat().st_mode))
    if 'code_tree' in over and (out.stat().st_mode & 0o777) != 0o700: refuse('directory mode differs')
    for name in sorted(member_directories(members) - {'.'}, key=lambda n: (len(Path(n).parts), n)):
        fs.mkdir(out / name, stat.S_IMODE((kit / name).stat().st_mode))
    for name in members:
        if name in missing or (changing and name == 'k/' + old_key + '.json'): continue
        fs.copy(kit / name, out / name, stat.S_IMODE((kit / name).stat().st_mode))
    if changing:
        for name in ('o', 'runs'): fs.mkdir(out / name, 0o700)
""" + s[end:]
s=s.replace("[json.loads(p.read_text()) for p in sorted((kit / 'k').iterdir()) if p.suffix == '.json' and p.is_file()]",
            "[json.loads((kit / n).read_text()) for n in manifest_members(kit) if n.startswith('k/') and n.endswith('.json') and n not in missing]")
s=s.replace("if (kit / 'k' / name).exists():", "if 'k/' + name in src_inventory:")
s=s.replace("fs.write(out / 'k' / (key + '.json'), cfg)", "fs.write(out / 'k' / (key + '.json'), cfg, stat.S_IMODE((kit / 'k' / (old_key + '.json')).stat().st_mode))")
s=s.replace("    (out / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\\n' for k, v in sorted(inventory.items())))", "    fs.text(out / 'SHA256SUMS.txt', ''.join(f'{v}  {k}\\n' for k, v in sorted(inventory.items())), stat.S_IMODE((kit / 'SHA256SUMS.txt').stat().st_mode))")
s=s.replace("    if changing:  # explicit placeholder: a.py refuses until an independent content scan replaces it\n        fs.write(out / 'ANON_OK.json',", "    # Never inherit an unmanifested certificate; require independent content review.\n    fs.write(out / 'ANON_OK.json',")
s=s.replace('    return dict(config_key=key,', "    if not changing: out.chmod(stat.S_IMODE(kit.stat().st_mode))\n    return dict(config_key=key,")
Path('tools/derive_kit_h1.py').write_text(s)
