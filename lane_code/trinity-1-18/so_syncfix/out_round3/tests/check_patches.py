"""Replay both patch deliveries on private tmp_* trees; never invoke Git or SSH."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

package = Path(__file__).resolve().parents[1]
work = Path(os.environ['LCS_PATCH_WORK'])
work.mkdir(parents=True, exist_ok=True)
for mode in ('numbered', 'tools-only'):
    root = Path(tempfile.mkdtemp(prefix='tmp_' + mode + '_', dir=str(work)))
    (root / 'tools').mkdir()
    for line in (package / 'PREIMAGE.sha256').read_text().splitlines():
        unused, name = line.split(None, 1)
        (root / name).write_bytes((package / 'inputs' / Path(name).name).read_bytes())
    patches = sorted((package / 'patches').glob('*.diff')) if mode == 'numbered' else [package / 'INSTALL_TOOLS.diff']
    for patch in patches:
        result = subprocess.run(['patch', '--batch', '--fuzz=0', '--no-backup-if-mismatch', '-p1', '-i', str(patch)],
                                cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        if b'fuzz' in result.stdout or b'offset' in result.stdout:
            raise AssertionError(result.stdout)
    targets = list((package / 'tools').glob('*'))
    if mode == 'numbered':
        targets += list((package / 'tests').glob('*.py')) + list((package / 'inputs').glob('*'))
        targets += [package / name for name in ('install_tools.py', 'calibrate_budgets.py', 'owner_checks.py',
                    'install.sh', 'pre_enable.sh', 'calibrate.sh', 'enable.sh', 'PREIMAGE.sha256', 'POSTIMAGE.sha256')]
    for source in targets:
        target = root / source.relative_to(package)
        assert source.read_bytes() == target.read_bytes(), str(source)
        if target.suffix == '.sh':
            subprocess.check_call(['bash', '-n', str(target)])
        elif target.suffix == '.py':
            compile(target.read_bytes(), str(target), 'exec')
    print('%s: patches=%d files=%d bytes=identical syntax=OK fuzz=0 offsets=0' % (mode, len(patches), len(targets)))
print('PATCH REPLAY OK')
