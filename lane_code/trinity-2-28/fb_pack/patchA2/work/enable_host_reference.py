"""Expose the authenticated base at the host test's required sibling path."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
verification=ROOT/'out/BASE_VERIFICATION.json'
record=json.loads(verification.read_text())
entry=ROOT/'work/base/launch_r1/entry.py'
assert sha(entry)==record['results']['base']['input_files_sha256']['launch_r1/entry.py']
alias=ROOT/'work/tree_r1_base'
if not alias.exists():alias.symlink_to('base',target_is_directory=True)
assert alias.resolve()==ROOT/'work/base'
inputs=[Path(__file__),verification,entry,ROOT/'work/live/tests/test_host24j.py']
(ROOT/'out/HOST_REFERENCE.json').write_text(json.dumps(dict(status='PASS',
    command='env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B work/enable_host_reference.py',
    inputs_sha256={str(p):sha(p) for p in inputs},reference=str(alias),target=str(alias.resolve())),indent=2)+'\n')
(ROOT/'STATUS.md').write_text('The host mode-p comparison now has its required sibling reference path, linked to the authenticated 57a1f14d base. The final live suite remains in progress; both MUST fixes and all focused patch regressions pass.\n')
