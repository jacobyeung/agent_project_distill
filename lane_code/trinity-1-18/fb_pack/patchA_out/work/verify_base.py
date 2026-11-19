"""Copy the supplied local tree and verify it without creating a source seal."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24')
EXPECTED = '57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
COMMAND = 'env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B work/verify_base.py'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

for name in ('base', 'new'):
    target = ROOT / 'work' / name
    if not target.exists():
        shutil.copytree(SOURCE / 'work/tree_r1', target, symlinks=True)

sys.path.insert(0, str(ROOT / 'work/base'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest

listing = SOURCE / 'out/TREE_FILES.sha256'
seal_path = SOURCE / 'out/TREE_SEAL.json'
expected_files = {name: value for value, name in
                  (line.split('  ', 1) for line in listing.read_text().splitlines())}
seal = json.loads(seal_path.read_text())
results = {}
for name in ('base', 'new'):
    actual = inventory(ROOT / 'work' / name)
    mismatches = [dict(path=p, expected_sha256=expected_files.get(p), actual_sha256=actual.get(p))
                  for p in sorted(set(actual) | set(expected_files))
                  if actual.get(p) != expected_files.get(p)]
    results[name] = dict(files=len(actual), tree_sha256=digest(actual),
                         matches=(actual == expected_files and digest(actual) == EXPECTED),
                         mismatches=mismatches, input_files_sha256=actual)
result = dict(status='PASS' if all(r['matches'] for r in results.values()) else 'BLOCKED_UNSEALED_BASE',
              command=COMMAND, expected_tree_sha256=EXPECTED,
              declared_seal=seal, listed_files=len(expected_files), listed_tree_sha256=digest(expected_files),
              inputs_sha256={str(p): sha(p) for p in (listing, seal_path, Path(__file__),
                  ROOT/'work/base/student_pilot/source_seal.py', ROOT/'work/base/student_pilot/p3_provenance.py')},
              results=results,
              recovery_archive=dict(path=str(SOURCE/'out/tree_rebuild_b24e_aa15b435.tar'),
                                    status='PRESENT' if (SOURCE/'out/tree_rebuild_b24e_aa15b435.tar').is_file() else 'MISSING'))
(ROOT/'out/BASE_VERIFICATION.json').write_text(json.dumps(result, indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Base verification: '+result['status']+'. Both local copies were checked with the kit inventory and digest functions. '+str(len(results['base']['mismatches']))+' files differ from the supplied seal list. Details and all input hashes are in out/BASE_VERIFICATION.json.\n')
print(json.dumps({k: v for k, v in result.items() if k != 'results'}, indent=2))
for name, r in results.items():
    print(name, json.dumps({k:v for k,v in r.items() if k != 'input_files_sha256'}, indent=2))
