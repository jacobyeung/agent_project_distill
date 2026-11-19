"""Record exact commands, outputs, timestamps and exit codes for final validation."""
import json
import os
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
logs = ROOT / 'out/round4_logs'
records = json.loads((logs / 'commands.json').read_text())
python = ['nice', '-n', '10', '/scratch/jjyeung/envs/p1cpu/bin/python', '-I', '-s', '-B']
runner = python + ['work/run_tests.py']
core = ['--tool', 'work/patchcheck_round4_core', '--tests', 'work/patchcheck_round4_core/tests']
full = ['--tool', 'work/patchcheck_round4_full', '--tests', 'work/patchcheck_round4_full/tests']
commands = [
    ('package', python + ['work/package_round4.py']),
    ('core_tests', runner + core + ['test_review2', 'test_review3', 'test_synthetic', 'test_no_leftovers']),
    ('full_tests', ['nice', '-n', '10', '/usr/bin/time', '-f',
                    'MEASURED_MAX_RSS_KIB=%M\nMEASURED_ELAPSED_SECONDS=%e\nEXIT_CODE=%x'] +
                    python[3:] + ['work/run_tests.py'] + full +
                    ['test_review2', 'test_review3', 'test_new_read_wrapper', 'test_kit_alias_proof',
                     'test_synthetic', 'test_no_leftovers']),
    ('existing_enabled', runner + full + ['--enable-review2', 'test_synthetic']),
    ('default_compat', python + ['work/check_default_compat.py']),
    ('published_snapshot_audit', python + ['work/audit_round4.py']),
    ('wrapper_syntax', ['nice', '-n', '10', 'bash', '-n', 'work/patchcheck_round4_full/add_read.sh']),
]
for name, command in commands:
    stamp = subprocess.check_output(['date', '-u'], text=True).strip()
    print(stamp, flush=True)
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    path = logs / (name + '.txt')
    path.write_bytes(result.stdout)
    records.append(dict(name=name, utc=stamp, command=shlex.join(command), exit_code=result.returncode,
                        output=str(path.relative_to(ROOT))))
    (logs / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
    print(name, 'exit', result.returncode, flush=True)
    print(result.stdout.decode(), end='', flush=True)
    assert result.returncode == 0, name
(ROOT / 'work/STATUS.md').write_text(subprocess.check_output(['date', '-u'], text=True) +
    'All final checks passed: independent core patch, full patch stack, enabled existing suite, '
    'default-byte compatibility, and local saved-index/task audit. Owner proof was tested only '
    'on synthetic workspace fixtures. Packaging complete; report/manifest pending.\n')
