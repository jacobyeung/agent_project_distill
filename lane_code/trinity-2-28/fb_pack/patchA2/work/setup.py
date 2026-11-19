import hashlib, json, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'work/base'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def record(name, value):
    value['command'] = 'env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B work/setup.py'
    value.setdefault('inputs_sha256', {})[str(Path(__file__))] = sha(__file__)
    (ROOT/'out'/name).write_text(json.dumps(value, indent=2)+'\n')
a = ROOT.parent/'patchA'
patch = a/'out/PATCH_A.patch'
h = sha(patch)
assert h.startswith('b95c1c61') and h.endswith('de477'), h
shutil.copytree(ROOT/'work/base', ROOT/'work/patch_a')
for n in ('new', 'patch_a'):
    r = subprocess.run(['patch','--batch','--fuzz=0','--no-backup-if-mismatch','-p1','-d',str(ROOT/'work'/n)], input=patch.read_bytes(), capture_output=True)
    (ROOT/'out'/('apply_A_'+n+'.log')).write_bytes(r.stdout+r.stderr)
    assert r.returncode == 0, r.stdout
expected = json.loads((a/'out/FILES_TOUCHED.json').read_text())
for f in expected['files']:
    assert sha(ROOT/'work/new'/f['path']) == f['new_sha256'], f['path']
record('PATCH_A_INPUT.json', dict(status='PASS', patch_sha256=h, inputs_sha256={str(p):sha(p) for p in (patch,a/'out/FILES_TOUCHED.json',a/'out/REPORT.md',a/'out/TESTS.json',a/'work/run_tests.py',a/'work/verify_base.py')}, files=expected['files']))
live = Path('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l')
sealpath = live/'out24j/TREE24J_SEAL.json'
seal = json.loads(sealpath.read_text())
candidates = {}
chosen = None
for n in ('tree_r1_base', 'tree_r1'):
    actual = inventory(live/'work'/n)
    candidates[n] = dict(files=len(actual), tree_sha256=digest(actual), matches=actual==seal['files'])
    if actual == seal['files']:
        chosen = live/'work'/n
        break
assert chosen is not None, candidates
assert seal['tree_sha256'] == '189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710'
assert digest(actual) == seal['tree_sha256']
shutil.copytree(chosen, ROOT/'work/live_base')
shutil.copytree(chosen, ROOT/'work/live')
assert inventory(ROOT/'work/live') == actual
base = inventory(ROOT/'work/base')
changed = [p for p in sorted(set(base)|set(actual)) if base.get(p) != actual.get(p)]
record('LIVE_VERIFICATION.json', dict(status='PASS', original_requested_seal='MISSING: '+str(live/'out/TREE_SEAL.json'), authenticated_seal=str(sealpath), candidates=candidates, source=str(chosen), tree_sha256=digest(actual), files=len(actual), differs_from_base=changed, inputs_sha256={str(sealpath):sha(sealpath), **{str(chosen/p):h for p,h in actual.items()}}, file_hashes=actual))
camera = ROOT.parent/'ro/orch_n30/fb_pack/cam/out/rows/camera_wording.jsonl'
standin = ROOT.parent/'ro/orch_n30/fb_pack/route/out/rows/camera_wording.jsonl'
assert camera.is_file(), 'MISSING: '+str(camera)
ch = sha(camera)
assert ch.startswith('e8cbda99'), ch
record('CAMERA_INPUT.json', dict(status='PASS', final_path=str(camera), final_sha256=ch, standin_path=str(standin), standin_sha256=sha(standin), inputs_sha256={str(camera):ch,str(standin):sha(standin)}))
(ROOT/'STATUS.md').write_text('Both source trees and PATCH_A are authenticated. The live copy matches the 189df6ac seal; the final camera rows match the supplied e8cbda99 prefix. Local base, PATCH_A, new and live trees are ready for changes and regression tests.\n')
print(json.dumps(dict(patch=h, live=candidates, live_changes=changed, camera=ch)))
