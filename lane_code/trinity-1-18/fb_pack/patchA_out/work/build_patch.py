"""Build and apply-check an overlay against the authenticated base; do not seal it."""
import difflib, hashlib, json, shutil, subprocess, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'out'
BASE, NEW = ROOT/'work/base', ROOT/'work/new'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
verification = json.loads((OUT/'BASE_VERIFICATION.json').read_text())
assert verification['status'] == 'PASS'
expected = verification['results']['base']['input_files_sha256']
for name, h in expected.items():
    assert sha(BASE/name) == h, 'SEALED_BASE_CHANGED:'+name
names = sorted(set(expected) | {'tests/test_r1_subset.py'})
changed, patch = [], []
for name in names:
    a, b = BASE/name, NEW/name
    old, new = a.read_bytes() if a.exists() else b'', b.read_bytes()
    if old == new: continue
    changed.append(dict(path=name, base_sha256=sha(a) if a.exists() else None,
                        new_sha256=sha(b)))
    patch.extend(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
        fromfile='a/'+name if a.exists() else '/dev/null', tofile='b/'+name))
(OUT/'PATCH_A.patch').write_text(''.join(patch))
inputs = {str(OUT/'BASE_VERIFICATION.json'):sha(OUT/'BASE_VERIFICATION.json'), str(Path(__file__)):sha(__file__)}
for entry in changed:
    for root, field in ((BASE,'base_sha256'), (NEW,'new_sha256')):
        if entry[field] is not None: inputs[str(root/entry['path'])] = entry[field]
record = dict(status='PATCH_ONLY_NOT_RESEALED', command='env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B work/build_patch.py',
    base_tree_sha256=verification['expected_tree_sha256'], inputs_sha256=inputs, files=changed)
(OUT/'FILES_TOUCHED.json').write_text(json.dumps(record, indent=2)+'\n')
check = Path(tempfile.mkdtemp(prefix='apply_check_', dir=ROOT/'work'))
shutil.copytree(BASE, check, dirs_exist_ok=True)
command = ['patch','--batch','--fuzz=0','-p1','-d',str(check)]
result = subprocess.run(command, input=(OUT/'PATCH_A.patch').read_bytes(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(OUT/'patch_apply.log').write_bytes(result.stdout)
assert result.returncode == 0, result.stdout.decode()
assert all(sha(check/name) == sha(NEW/name) for name in names)
(OUT/'PATCH_VALIDATION.json').write_text(json.dumps(dict(status='PASS',
    command=record['command'], patch_command=command,
    inputs_sha256={str(OUT/'PATCH_A.patch'):sha(OUT/'PATCH_A.patch'),
                  str(OUT/'FILES_TOUCHED.json'):sha(OUT/'FILES_TOUCHED.json'), **inputs},
    checked_files=len(names), changed_files=len(changed), exact_application=True), indent=2)+'\n')
(ROOT/'STATUS.md').write_text(f'The overlay changes {len(changed)} files and applies without fuzz to the verified base. All {len(names)} resulting source files match work/new. The full CPU suites remain in progress; real composition and fixture-dependent alias tests have missing inputs.\n')
print(json.dumps(dict(changed_files=len(changed), checked_files=len(names), patch_sha256=sha(OUT/'PATCH_A.patch'))))
