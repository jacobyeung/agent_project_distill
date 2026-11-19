from pathlib import Path
import hashlib, json, shutil
W = Path(__file__).resolve().parents[1]
D = W.parent / 'donor2'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs = {str(Path(__file__).resolve()): sha(__file__)}
manifest = D/'out/TREE_FILES.sha256'
rows = {line.split('  ', 1)[1]: line.split('  ', 1)[0] for line in manifest.read_text().splitlines()}
inputs[str(manifest)] = sha(manifest)
base_seal = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert base_seal.startswith('57a1f14d')
live_report = D/'out/LIVE_VERIFY.json'
live = json.loads(live_report.read_text())
inputs[str(live_report)] = sha(live_report)
prefix = live['verified_location'] + '/'
live_rows = {p[len(prefix):]: h for p, h in live['input_sha256'].items() if p.startswith(prefix)}
live_seal = hashlib.sha256(json.dumps(live_rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert live_seal == live['tree_sha256'] and live_seal.startswith('189df6ac')
for label, expected in [('base', rows), ('live_base', live_rows)]:
    for name, h in expected.items():
        src = D/'work'/label/name
        assert sha(src) == h, src
        inputs[str(src)] = h
        for dest_label in ([label, 'live'] if label == 'live_base' else [label]):
            dst = W/'work'/dest_label/name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
touched = D/'out/FILES_TOUCHED.json'
inputs[str(touched)] = sha(touched)
new_rows = dict(rows)
new_rows.update({e['path']: e['new_sha256'] for e in json.loads(touched.read_text())['files']})
for name, h in new_rows.items():
    src = D/'work/new'/name
    assert sha(src) == h, src
    inputs[str(src)] = h
    dst = W/'work/new'/name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
for name in ['TREE_FILES.sha256', 'REAL_WEIGHT_COMMAND.sh', 'READER_REQUEST.md']:
    src = D/'out'/name
    shutil.copyfile(src, W/'out'/name)
    inputs[str(src)] = sha(src)
for name in ['run_unit.py', 'run_focused.py', 'parity_full.py']:
    src = D/'code'/name
    shutil.copyfile(src, W/'code'/name)
    inputs[str(src)] = sha(src)
result = dict(input_sha256=inputs, base_tree_sha256=base_seal, live_tree_sha256=live_seal,
              base_files=len(rows), live_files=len(live_rows), new_files=len(new_rows),
              command='python -B code/stage.py', status='PASS')
(W/'out/STAGING.json').write_text(json.dumps(result, indent=2)+'\n')
(W/'STATUS.md').write_text('The base and live seals match their supplied manifests. Local copies of the base, donor2 overlay and live tree are staged. M4 requires a reader recipe and runtime test change; donor training code remains unchanged.\n')
print({k:v for k,v in result.items() if k != 'input_sha256'})
