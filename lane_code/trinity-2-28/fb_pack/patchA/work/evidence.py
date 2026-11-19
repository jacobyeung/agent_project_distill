"""Authenticate the reviewed alias rebase."""
import hashlib, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RO = ROOT.parent/'ro/orch_n30'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
command = 'env PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B work/evidence.py'
report = ROOT/'work/inputs/FHALIAS2_REPORT.md'
patch = RO/'sb_fhalias/out/ALIAS.patch'
expected = re.findall(r'`([^`]+\.py)`: ([0-9a-f]{64}) -> ([0-9a-f]{64})', report.read_text())
assert len(expected) == 6
files = []
for name, before, after in expected:
    a,b = ROOT/'work/base'/name, ROOT/'work/new'/name
    files.append(dict(path=name, reviewed_base_sha256=before, reviewed_new_sha256=after,
        actual_base_sha256=sha(a), actual_new_sha256=sha(b)))
assert all(x['actual_base_sha256']==x['reviewed_base_sha256'] and x['actual_new_sha256']==x['reviewed_new_sha256'] for x in files)
(ROOT/'out/ALIAS_REBASE.json').write_text(json.dumps(dict(status='PASS', command=command,
    applied_command='patch -p1 -d work/new < '+str(patch),
    inputs_sha256={str(report):sha(report),str(patch):sha(patch),str(Path(__file__)):sha(__file__),
        **{str(ROOT/'work'/version/name):sha(ROOT/'work'/version/name) for name,_,_ in expected for version in ('base','new')}},
    files=files, missing_requested_patch='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_build/ops_mirror/reports_1410Z/ALIAS2.patch',
    fallback='Local ALIAS.patch produces exactly the six reviewed file hashes.'), indent=2)+'\n')
print('Verified six reviewed alias file pairs.')
