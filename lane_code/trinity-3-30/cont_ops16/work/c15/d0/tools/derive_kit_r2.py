"""Derive a data-only kit from sealed kit 07ca49df's own records: same trainer tree, b/ gate, job scripts and 7.json;
new row-store pins (VQA, routing), pool selection, dev scene exclusions, init artifact and run identity.
Serialization follows launch_s1/build.py (sorted compact JSON plus newline; config file name = sha256(config)[:8];
launch source_seal as b/g.py checks it).

Usage: derive_kit.py KIT_DIR OUT_DIR OVERRIDES.json
OVERRIDES keys (anything else is refused):
  run_key, kit_key, persistent_run_root   all three required, and new, whenever any input changes
  config: {streams: {vqa?, routing?}, init_artifact?, s1_routing: {selection?, catalog?}?, dev_scene_exclusions?,
           scene_coverage?}
  deployment: {init?, tars?, extra?}       replacements of k/0.json entries
  add_k: {name: {path, sha256}}            new small records; names from ADD_K only
  status: BLOCKED (default) | READY        READY needs review.json, staging.json and 4.json in add_k, bound to the new identity
  fixture: true                            allow source-kit files listed in SHA256SUMS to be absent (tests only; output is
                                           marked FIXTURE and can never be READY)
An empty OVERRIDES ({"fixture": true} when big tars are absent) reproduces the kit's k/ records byte for byte."""
import copy, hashlib, json, re, shutil, sys
from pathlib import Path

def enc(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)
def digest(v): return hashlib.sha256(enc(v).encode()).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, v): Path(p).write_text(enc(v) + '\n')
def identity(cfg):  # b/i.py identity, same logic
    value = {k: v for k, v in cfg.items() if k not in ('preparation', 'admission', 'authorization', 'milestone_gate')}
    if 'readout' in value:
        value['readout'] = {k: v for k, v in value['readout'].items() if k != 'contiguous_clips'}
    if value.get('frame_layout') == 'spread': value.pop('frame_layout')
    return digest(value)

HEX8 = re.compile('[0-9a-f]{8}')
TOP = {'run_key', 'kit_key', 'persistent_run_root', 'config', 'deployment', 'add_k', 'status', 'fixture'}
CONFIG = {'streams', 'init_artifact', 's1_routing', 'dev_scene_exclusions', 'scene_coverage'}
STREAMS = {'vqa', 'routing'}
S1_ROUTING = {'selection', 'catalog'}
DEPLOYMENT = {'init', 'tars', 'extra'}
ADD_K = {'review.json', 'staging.json', '4.json', 'pool_selection.json', 'dev_scene_exclusions.json'}
AS = '/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
AL = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/'
KIT_LOGICAL = AS + 'ap/8865619b/k/'

def refuse(why): raise ValueError('derive_kit: ' + why)

def staged_files(cur):
    """Logical relative path -> sha256 for everything k/0.json stages from tars and extra."""
    out = {}
    for t in cur.get('tars', []):
        out.update(t['files'])
    for e in cur.get('extra', []):
        for prefix in (AS, AL):
            if e['dest'].startswith(prefix): out[e['dest'][len(prefix):]] = e['sha256']
    return out

def rel(path):
    for prefix in (AS, AL):
        if path.startswith(prefix): return path[len(prefix):]
    refuse('pin outside the code-aws prefixes: ' + path)

def derive(kit, out, over):
    kit, out = Path(kit), Path(out)
    if set(over) - TOP: refuse('unknown override keys ' + str(sorted(set(over) - TOP)))
    if set(over.get('config', {})) - CONFIG: refuse('config keys outside the data-only set ' + str(sorted(set(over['config']) - CONFIG)))
    if set(over.get('config', {}).get('streams', {})) - STREAMS: refuse('only the vqa and routing streams may change')
    if set(over.get('config', {}).get('s1_routing', {})) - S1_ROUTING: refuse('only s1_routing.selection and .catalog may change')
    if set(over.get('deployment', {})) - DEPLOYMENT: refuse('deployment keys outside init/tars/extra')
    for name in over.get('add_k', {}):
        if name not in ADD_K: refuse('add_k name not allowed: ' + name)
    fixture = over.get('fixture') is True
    status = over.get('status', 'BLOCKED')
    if status not in ('BLOCKED', 'READY'): refuse('status must be BLOCKED or READY')
    if fixture and status == 'READY': refuse('a fixture derivation can never be READY')
    # Source kit must match its own sealed manifest (absent big files allowed only for fixtures).
    missing = []
    for line in (kit / 'SHA256SUMS.txt').read_text().splitlines():
        want, name = line.split('  ', 1)
        p = kit / name
        if not p.is_file(): missing.append(name); continue
        if sha(p) != want: refuse('source kit file differs from its manifest: ' + name)
    if missing and not fixture: refuse('source kit files absent: ' + ', '.join(missing))
    launch = json.loads((kit / 'k/launch.json').read_text())
    old_key = json.loads((kit / 'k/1.json').read_text())['0']
    base_cfg = json.loads((kit / 'k' / (old_key + '.json')).read_text())
    base_cur = json.loads((kit / 'k/0.json').read_text())
    old_run, old_kit, old_root = launch['run_key'], launch['kit_key'], launch['persistent_run_root']
    changing = bool(over.get('config') or over.get('deployment') or over.get('add_k'))
    run, kit_key, root = (over.get(k, d) for k, d in (('run_key', old_run), ('kit_key', old_kit), ('persistent_run_root', old_root)))
    if changing and (run == old_run or kit_key == old_kit or root == old_root):
        refuse('changed inputs need a new run_key, kit_key and persistent_run_root')
    for key in (run, kit_key):
        if not HEX8.fullmatch(key): refuse('keys must be eight hex digits')
    if not isinstance(root, str) or not root.startswith('/') or '..' in root.split('/'): refuse('persistent_run_root must be absolute')
    if changing and '/home/' in root: refuse('persistent_run_root must not be under /home')

    cfg, cur = copy.deepcopy(base_cfg), copy.deepcopy(base_cur)
    if run != old_run:
        for field in ('output', 'preparation_output'):
            cfg[field] = re.sub('/' + old_run + '$', '/' + run, cfg[field])
            if not cfg[field].endswith('/' + run): refuse(field + ' does not end in the run key')
    oc = over.get('config', {})
    if 'streams' in oc: cfg['streams'] = {**cfg['streams'], **oc['streams']}
    if 's1_routing' in oc: cfg['s1_routing'] = {**cfg['s1_routing'], **oc['s1_routing']}
    for k in ('init_artifact', 'dev_scene_exclusions', 'scene_coverage'):
        if k in oc: cfg[k] = oc[k]
    for k, v in over.get('deployment', {}).items(): cur[k] = v

    out.mkdir()
    shutil.copytree(kit / 'b', out / 'b')
    for name in ('job.sh', 'job8.sh'): shutil.copy2(kit / name, out / name)
    (out / 'k').mkdir(); (out / 'o').mkdir(); (out / 'runs').mkdir()
    for p in sorted((kit / 'k').iterdir()):
        if p.name in ('launch.json', '1.json', '0.json', old_key + '.json'): continue
        shutil.copy2(p, out / 'k' / p.name)
    for name, pin in over.get('add_k', {}).items():
        if sha(pin['path']) != pin['sha256']: refuse('add_k pin differs: ' + name)
        shutil.copyfile(pin['path'], out / 'k' / name)
    if 'review.json' in over.get('add_k', {}):
        cfg['admission'] = dict(path=KIT_LOGICAL + 'review.json', sha256=sha(out / 'k/review.json'))

    # Dependency chain: every changed config pin must be staged, and config and deployment must agree.
    staged = staged_files(cur)
    for name in oc.get('streams', {}):
        pin = cfg['streams'][name]
        if staged.get(rel(pin['path'])) != pin['sha256']: refuse(f'stream {name} receipt is not staged by k/0.json at its pin')
    if 'init_artifact' in oc:
        a = cfg['init_artifact']['artifact']
        if cur.get('init') != dict(file=a['path'], sha256=a['sha256']): refuse('config init_artifact and k/0.json init differ')
        if staged.get(rel(a['path'])) != a['sha256']: refuse('init artifact.json is not staged by k/0.json tars')
        if any(k.startswith('ap/f2ad01ad/runs/49becb79/m200/') for k in staged) and base_cfg['init_artifact'] != cfg['init_artifact']:
            refuse('the old init (CP1 m200) is still staged')
    if 'init' in over.get('deployment', {}) and 'init_artifact' not in oc: refuse('k/0.json init changed without config init_artifact')
    for name, key in (('pool_selection.json', 'selection'), ('dev_scene_exclusions.json', None)):
        if name in over.get('add_k', {}):
            want = dict(path=KIT_LOGICAL + name, sha256=sha(out / 'k' / name))
            got = cfg['s1_routing']['selection'] if key else cfg['dev_scene_exclusions']
            if got != want: refuse(f'{name} replaced but the config does not pin it')
            if key and cfg['s1_routing']['catalog'].get(want['sha256']) != want['path']: refuse('pool selection missing from the catalog')
    if 'selection' in oc.get('s1_routing', {}) and 'pool_selection.json' not in over.get('add_k', {}): refuse('selection pin changed without the new k/pool_selection.json')
    for value in (cfg['streams'], cfg.get('init_artifact')):
        text = enc(value)
        for old in ({} if run == old_run else {k: v for k, v in base_cfg['streams'].items() if k in oc.get('streams', {})}).values():
            if enc(old) in text: refuse('a changed stream still carries its old pin')

    key = digest(cfg)[:8]
    write(out / 'k' / (key + '.json'), cfg)
    write(out / 'k/1.json', {'0': key})
    write(out / 'k/0.json', cur)
    code = json.loads((kit / 'k/7.json').read_text())
    seal = dict(schema='s1-run-seal-v1', tree_sha256=code['tree_sha256'], config_sha256=identity(cfg), archive=code['archive'])
    launch = copy.deepcopy(launch)
    launch.update(config=dict(file='k/' + key + '.json', sha256=sha(out / 'k' / (key + '.json'))), run_key=run, kit_key=kit_key,
                  run_directory=f'/tmp/jjyeung/okit_8865619b/runs/{run}', source_seal={**seal, 'sha256': digest(seal)},
                  persistent_run_root=root, inherited_streams=copy.deepcopy(cfg['streams']),
                  source_selection=copy.deepcopy(cfg['s1_routing']['selection']))
    if 'in_job_admission' in launch:
        launch['in_job_admission']['directory'] = cfg['output'] + '/inputs'
    for k in ('review', 'staging', 'archive', 'first_batch'):
        if k in launch and (out / 'k' / (k + '.json')).is_file():
            launch[k] = dict(file=f'k/{k}.json', sha256=sha(out / 'k' / (k + '.json')))
    if changing:
        if status == 'READY':
            ident = identity(cfg)
            for name in ('review.json', 'staging.json', '4.json'):
                if name not in over.get('add_k', {}): refuse('READY needs a new ' + name)
            if json.loads((out / 'k/review.json').read_text()).get('config_sha256') != ident: refuse('review does not bind the new identity')
            if json.loads((out / 'k/staging.json').read_text()).get('config_sha256') != ident: refuse('staging does not bind the new identity')
            if json.loads((out / 'k/4.json').read_text()).get('config_sha256') != ident: refuse('authorization does not bind the new identity')
        launch.update(status=status, production_authorized=status == 'READY')
    if fixture:
        launch['status'] = 'FIXTURE' if changing else launch['status']
    write(out / 'k/launch.json', launch)
    inventory = {str(p.relative_to(out)): sha(p) for part in ('b', 'k') for p in sorted((out / part).rglob('*')) if p.is_file()}
    inventory.update({n: sha(out / n) for n in ('job.sh', 'job8.sh')})
    (out / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(inventory.items())))
    if changing:  # explicit placeholder: a.py refuses until an independent content scan replaces it
        write(out / 'ANON_OK.json', dict(status='UNREVIEWED', hits=None, manifest_sha256=sha(out / 'SHA256SUMS.txt'), external=[],
                                         scope='integrity-manifest-only; independent-content-scan-not-supplied'))
    return dict(config_key=key, config_identity=identity(cfg), run_key=run, kit_key=kit_key, persistent_run_root=root,
                manifest_sha256=sha(out / 'SHA256SUMS.txt'), launch_status=launch.get('status'), absent_source_files=missing)

if __name__ == '__main__':
    print(json.dumps(derive(sys.argv[1], sys.argv[2], json.loads(Path(sys.argv[3]).read_text())), indent=1))
