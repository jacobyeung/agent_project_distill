import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT.parent
SOURCE = PACK/'ro/orch_n30/tree_rebuild10_w/w24/work/tree_r1'
EXPECTED = '57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1<<20), b''): h.update(block)
    return h.hexdigest()
def inventory(root):
    result = {}
    for directory, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in ('.git', '__pycache__', 'artifacts'))
        for name in sorted(names):
            p = Path(directory)/name
            assert not p.is_symlink() and p.stat().st_size < 16_000_000
            result[str(p.relative_to(root))] = sha(p)
    return result
def digest(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',',':'), allow_nan=False).encode()).hexdigest()
files = inventory(SOURCE)
assert digest(files) == EXPECTED, digest(files)
for name, value in files.items():
    dest = ROOT/'work/base'/name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE/name, dest)
patch = PACK/'patchA/out/PATCH_A.patch'
result = subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch)], cwd=ROOT/'work/base', text=True, capture_output=True)
(ROOT/'out/patch_A_apply.log').write_text(result.stdout+result.stderr)
assert result.returncode == 0, result.stdout+result.stderr
base = inventory(ROOT/'work/base')
shutil.copytree(ROOT/'work/base', ROOT/'work/new')
inputs = {str(SOURCE/name):value for name,value in files.items()}
inputs[str(patch)] = sha(patch)
inputs[str(Path(__file__))] = sha(__file__)
protected = {}
for lane in ('donor','prior2','camform'):
    p = PACK/lane/'out/FILES_TOUCHED.json'
    inputs[str(p)] = sha(p)
    protected[lane] = [f['path'] for f in json.loads(p.read_text())['files']]
record = dict(command='bash code/run.sh setup', input_sha256=inputs, base_files=files,
              expected_tree_sha256=EXPECTED, actual_tree_sha256=digest(files), base_plus_patchA_files=base,
              base_plus_patchA_sha256=digest(base), protected=protected, status='PASS')
(ROOT/'out/SETUP.json').write_text(json.dumps(record, indent=2)+'\n')
(ROOT/'STATUS.md').write_text(f'Stage 1: The {len(files)}-file base matches seal {EXPECTED}. PATCH_A applies without fuzz. The writable base and new trees are isolated inside this workspace; donor, prior2 and camform file scopes are recorded in out/SETUP.json. Implementation and CPU tests are pending.\n')
print('PASS', len(files), digest(files), digest(base))
