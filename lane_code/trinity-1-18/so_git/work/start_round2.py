"""Snapshot only the named, small delivery files. Never invoke Git."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

L = Path('/scratch/jjyeung/orch_n30/so_git')
base = L / 'work/review_round2_base'
source = L / 'work/review_round2_source'
names = ['tools/' + n for n in ('land_kit.py', 'land_kit.sh', 'sync_health.py',
         'sync_health.sh', 'sync_health_loop.sh', 'dry_count.py', 'dry_count.sh')]
names += ['tests/' + n for n in ('__init__.py', 'test_owner_tools.py', 'test_real_git_owner.py',
          'run_real_git_owner.sh', 'fixtures/lane_code_sync.sh', 'test_filter_shell_copies.py',
          'test_recover_boundary_remediation.py')]
names += ['GIT_OWNER.md', 'COVERAGE.md', 'REPORT.md', 'MANIFEST.json']
for root in (base, source):
    root.mkdir(exist_ok=False)
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(L / 'out' / name), str(target))
    for name in ('lane_code_filter.py', 'lane_code_scan.py', 'lane_code_sync.sh'):
        shutil.copyfile(str(L / 'in' / name), str(root / 'tools' / name))
    shutil.copyfile(str(L / 'work/review_round1_source/tools/recover_boundary_remediation.py'),
                    str(root / 'tools/recover_boundary_remediation.py'))

installed = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools')
pins = {}
for name in names:
    if not name.startswith('tools/'):
        continue
    path = installed / Path(name).name
    raw = path.read_bytes()
    assert raw == (base / name).read_bytes(), str(path) + ' changed since review'
    pins[str(path)] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
# This is a bounded read of one named script, not a tree scan.
raw = (installed / 'lane_code_sync.sh').read_bytes()
assert raw == (L / 'in/lane_code_sync.sh').read_bytes()
pins[str(installed / 'lane_code_sync.sh')] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
(L / 'out/evidence/round2_installed_base.json').write_text(json.dumps(pins, indent=2) + '\n')
now = subprocess.check_output(['date', '-u'], universal_newlines=True).strip()
(L / 'work/STATUS.md').write_text(now + ': Read complete verdict and binding prompts; pinned installed tools and unchanged hourly script. Working copies prepared. This round forbids Git; real-Git validation remains blocked. Review fixes require LCS_REVIEW2_FIXES=1; default behavior stays unchanged.\n')
print(now)
print('SNAPSHOT_AND_INSTALLED_PINS_OK', len(pins))
