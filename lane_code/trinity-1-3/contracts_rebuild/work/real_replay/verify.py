"""Verify artifacts from the G3T tower-gravity replay, not student-head gravity."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import os

L = Path('/scratch/jjyeung/orch_n30/contracts_rebuild')
O = L / 'out/real_replay'
SOURCE = 'G3T tower gravity, not student-head gravity'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def inventory(root):
    return {str(p.relative_to(root)): sha(p) for p in root.rglob('*') if p.is_file()}

base = L / 'work/base/work/base/tree_b01ce449'
sealed = L / 'work/trees/real_base'
patched = L / 'work/trees/real_patched'
assert inventory(base) == inventory(sealed), 'Sealed copy differs from supplied base'
# Locate the plan retained by the packet's verified application.
receipt = json.loads((O / 'PREPARATION.json').read_text())['patch_application']
original = Path(receipt.split('retained original: ')[1].strip())
plan = original.parent / 'plan'
post = subprocess.run([sys.executable, '-I', '-s', '-B',
    str(L / 'out/contract_hash_checks.py'), 'post', str(patched), str(plan)],
    capture_output=True, text=True)
assert post.returncode == 0, post.stdout + post.stderr

report_root = Path(os.environ.get('REPLAY_REPORT_DIR', str(O)))
report_path = report_root / 'REAL_GEOMETRY_REPLAY.json'
assert report_path.stat().st_size < 20_000_000
report = json.loads(report_path.read_text())
assert not report['totals']['assertion_failures']
assert report['totals']['captures'] == report['input_inventory']['npz_count']
assert report['input_inventory']['missing_npz'] == []
assert report['input_inventory']['missing_json'] == []
for row in report['captures']:
    for arm in row['modes'].values():
        assert arm['gravity_source'] == SOURCE
        assert arm['source'] == row['source']
    on = row['modes']['patched_on']
    assert on['heading_exposed'] == on['heading_geometrically_defined']

total_bytes = sum(p.stat().st_size for p in L.rglob('*') if p.is_file())
assert total_bytes < 3_000_000_000
result = dict(gravity_source=SOURCE,
    source=str(report_path), sealed_copy_matches_base=True,
    base_source=str(base), sealed_copy=str(sealed),
    patched_hash_validation=True, patch_plan_source=str(plan),
    workspace_source=str(L), workspace_bytes=total_bytes,
    assertions_passed=sum(v for k, v in report['totals']['checks'].items() if k.endswith('_passed')),
    artifact_sha256={str(p): sha(p) for p in (report_path, report_root/'REAL_GEOMETRY_REPLAY.md')},
    scripts_sha256={str(p):sha(p) for p in (L/'work/real_replay').glob('*.py')})
with (O / 'FINAL_VERIFICATION.json').open('x') as f:
    json.dump(result, f, indent=2)
print(json.dumps(result), flush=True)
