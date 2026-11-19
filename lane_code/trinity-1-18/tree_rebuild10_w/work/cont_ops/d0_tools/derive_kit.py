"""Derive a data-only kit from sealed kit 07ca49df's own records: same trainer tree, b/ gate, job scripts and 7.json;
new stream pins, init artifact, run identity and staging entries. Serialization follows launch_s1/build.py
(p3_provenance.write: sorted compact JSON plus newline; config file name = sha256(config)[:8]; launch source_seal as b/g.py checks).
Usage: derive_kit.py KIT_DIR OUT_DIR OVERRIDES.json   (OVERRIDES {} reproduces the kit's k/ records)."""
import copy, hashlib, json, re, shutil, sys
from pathlib import Path

def enc(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), allow_nan=False)
def digest(v): return hashlib.sha256(enc(v).encode()).hexdigest()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p, v): Path(p).write_text(enc(v) + '\n')
def identity(cfg):  # b/i.py identity, verbatim logic
    value = {k: v for k, v in cfg.items() if k not in ('preparation', 'admission', 'authorization', 'milestone_gate')}
    if 'readout' in value:
        value['readout'] = {k: v for k, v in value['readout'].items() if k != 'contiguous_clips'}
    if value.get('frame_layout') == 'spread': value.pop('frame_layout')
    return digest(value)
HEX8 = re.compile('[0-9a-f]{8}')

def derive(kit, out, over):
    kit, out = Path(kit), Path(out)
    launch = json.loads((kit / 'k/launch.json').read_text())
    old_key = json.loads((kit / 'k/1.json').read_text())['0']
    cfg = json.loads((kit / 'k' / (old_key + '.json')).read_text())
    cur = json.loads((kit / 'k/0.json').read_text())
    old_run = launch['run_key']; run = over.get('run_key', old_run); kit_key = over.get('kit_key', launch['kit_key'])
    for key in (run, kit_key):
        if not HEX8.fullmatch(key): raise ValueError('keys must be eight hex digits')
    out.mkdir()
    shutil.copytree(kit / 'b', out / 'b')
    for name in ('job.sh', 'job8.sh'): shutil.copy2(kit / name, out / name)
    (out / 'k').mkdir(); (out / 'o').mkdir(); (out / 'runs').mkdir()
    keep = set(over.get('drop_k', []))
    for p in sorted((kit / 'k').iterdir()):
        if p.name in ('launch.json', '1.json', '0.json', old_key + '.json') or p.name in keep: continue
        shutil.copy2(p, out / 'k' / p.name)
    for name, pin in over.get('add_k', {}).items():  # small new records (review.json, staging.json, ...)
        if sha(pin['path']) != pin['sha256']: raise ValueError('add_k pin differs: ' + name)
        shutil.copyfile(pin['path'], out / 'k' / name)
    cfg = copy.deepcopy(cfg)
    if run != old_run:
        for field in ('output', 'preparation_output'):
            cfg[field] = re.sub('/' + old_run + '$', '/' + run, cfg[field])
    for k, v in over.get('config', {}).items():
        if v is None: cfg.pop(k, None)
        else: cfg[k] = v
    if 'admission_file' in over:
        cfg['admission'] = dict(path=re.sub('[^/]+$', over['admission_file'], cfg['admission']['path']),
                                sha256=sha(out / 'k' / over['admission_file']))
    key = digest(cfg)[:8]
    write(out / 'k' / (key + '.json'), cfg)
    write(out / 'k/1.json', {'0': key})
    for k, v in over.get('deployment', {}).items():
        if v is None: cur.pop(k, None)
        else: cur[k] = v
    write(out / 'k/0.json', cur)
    launch = copy.deepcopy(launch)
    code = json.loads((kit / 'k/7.json').read_text())
    seal = dict(schema='s1-run-seal-v1', tree_sha256=code['tree_sha256'], config_sha256=identity(cfg), archive=code['archive'])
    launch.update(config=dict(file='k/' + key + '.json', sha256=sha(out / 'k' / (key + '.json'))), run_key=run, kit_key=kit_key,
                  run_directory=f'/tmp/jjyeung/okit_8865619b/runs/{run}', source_seal={**seal, 'sha256': digest(seal)})
    if 'in_job_admission' in launch:
        launch['in_job_admission']['directory'] = cfg['output'] + '/inputs'
    for k in ('persistent_run_root', 'status', 'production_authorized'):
        if k in over: launch[k] = over[k]
    for k in ('review', 'staging', 'archive', 'first_batch'):
        if k in launch and (out / 'k' / (k + '.json')).is_file():
            launch[k] = dict(file=f'k/{k}.json', sha256=sha(out / 'k' / (k + '.json')))
    write(out / 'k/launch.json', launch)
    inventory = {str(p.relative_to(out)): sha(p) for part in ('b', 'k') for p in sorted((out / part).rglob('*')) if p.is_file()}
    inventory.update({n: sha(out / n) for n in ('job.sh', 'job8.sh')})
    (out / 'SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\n' for k, v in sorted(inventory.items())))
    return dict(config_key=key, config_identity=identity(cfg), run_key=run, kit_key=kit_key,
                manifest_sha256=sha(out / 'SHA256SUMS.txt'), launch_status=launch.get('status'))

if __name__ == '__main__':
    print(json.dumps(derive(sys.argv[1], sys.argv[2], json.loads(Path(sys.argv[3]).read_text())), indent=1))
