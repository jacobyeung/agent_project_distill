"""Exercise installation/rollback only in workspace/work/tmp_* with a fake hostname."""
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PACKAGE = Path(__file__).resolve().parents[1]
WORKSPACE = PACKAGE.parent
NAMES = ('lane_code_filter.py', 'dry_count.py')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def seal(package):
    (package / 'POSTIMAGE.sha256').write_text(''.join(
        '%s  tools/%s\n' % (sha((package / 'tools' / name).read_bytes()), name)
        for name in sorted(NAMES)))
    (package / 'SHA256SUMS').write_text(''.join(
        '%s  %s\n' % (sha(path.read_bytes()), path.relative_to(package).as_posix())
        for path in sorted(package.rglob('*')) if path.is_file() and path.name != 'SHA256SUMS'))


def main():
    root = Path(tempfile.mkdtemp(prefix='tmp_install_', dir=str(WORKSPACE / 'work')))
    package, base, state, commands = [root / name for name in ('package', 'base', 'state', 'bin')]
    shutil.copytree(str(PACKAGE), str(package))
    (base / 'tools').mkdir(parents=True)
    state.mkdir(); commands.mkdir()
    original = {}
    for name in NAMES:
        original[name] = (WORKSPACE / 'in/tools' / name).read_bytes()
        (base / 'tools' / name).write_bytes(original[name])
    (base / 'tools/lane_code_filter.py').chmod(0o750)
    (base / 'tools/dry_count.py').chmod(0o640)
    (state / 'LCS_ROBUST_SYNC').write_text('1\n')
    host = commands / 'hostname'
    host.write_text('#!/bin/sh\necho trinity-2-28\n'); host.chmod(0o755)
    env = dict(os.environ, B=str(base), S=str(state), LCS_ROBUST_SYNC='1', CUDA_VISIBLE_DEVICES='',
               PATH=str(commands) + os.pathsep + os.environ['PATH'])
    def invoke(script='install.sh', arguments=(), expected=0, use_package=package):
        result = subprocess.run(['bash', '-eu', str(use_package / script)] + list(arguments),
                                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        assert result.returncode == expected, (result.returncode, result.stdout, result.stderr)
        return result
    def pre_unchanged():
        assert all((base / 'tools' / name).read_bytes() == original[name] for name in NAMES)
    result = invoke(expected=2)
    assert b'only on trinity-3-30' in result.stderr
    pre_unchanged()
    assert not (state / 'install-backups').exists()
    print('PASS install/rollback hostname gate refuses trinity-2-28')
    host.write_text('#!/bin/sh\necho trinity-3-30\n')
    with (state / '.sync.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert b'holds the lock' in invoke(expected=3).stdout
        assert b'holds the lock' in invoke('rollback.sh', [str(state / 'install-backups/absent')], expected=3).stdout
    pre_unchanged()
    print('PASS install and rollback refuse held lock with exit 3')
    checksum_target = package / 'tools/lane_code_filter.py'
    good = checksum_target.read_bytes()
    checksum_target.write_bytes(good + b'\n# damaged package\n')
    invoke(expected=2); pre_unchanged()
    checksum_target.write_bytes(good)
    (base / 'tools/dry_count.py').write_bytes(original['dry_count.py'] + b'\n# changed preimage\n')
    result = invoke(expected=2)
    assert b'preimage/postimage mismatch' in result.stderr
    (base / 'tools/dry_count.py').write_bytes(original['dry_count.py'])
    print('PASS package checksum and installed PREIMAGE mismatches refuse writes')
    bad = root / 'bad_package'
    shutil.copytree(str(package), str(bad))
    (bad / 'tools/dry_count.py').write_text('this is invalid python !\n')
    seal(bad)
    invoke(expected=2, use_package=bad); pre_unchanged()
    print('PASS syntax error leaves both installed files unchanged after staging temporaries')
    result = invoke()
    assert b'INSTALL OK' in result.stdout
    backups = [line[7:] for line in result.stdout.decode().splitlines() if line.startswith('BACKUP ')]
    assert len(backups) == 1
    backup = Path(backups[0])
    assert (backup / 'preimage.tar').is_file()
    assert (backup / 'PREIMAGE.sha256').read_bytes() == (package / 'PREIMAGE.sha256').read_bytes()
    for name in NAMES:
        assert (base / 'tools' / name).read_bytes() == (package / 'tools' / name).read_bytes()
    assert ((base / 'tools/lane_code_filter.py').stat().st_mode & 0o777) == 0o750
    assert ((base / 'tools/dry_count.py').stat().st_mode & 0o777) == 0o640
    assert (state / 'LCS_ROBUST_SYNC').read_text() == '1\n'
    print('PASS install: verified backup, complete tool replacement, POSTIMAGE, modes; robust mode stays ON')
    host.write_text('#!/bin/sh\necho trinity-2-28\n')
    assert b'only on trinity-3-30' in invoke('rollback.sh', [str(backup)], expected=2).stderr
    host.write_text('#!/bin/sh\necho trinity-3-30\n')
    changed = base / 'tools/dry_count.py'
    good = changed.read_bytes()
    changed.write_bytes(good + b'\n# owner edit\n')
    assert b'differs from both' in invoke('rollback.sh', [str(backup)], expected=2).stderr
    assert changed.read_bytes() == good + b'\n# owner edit\n'
    changed.write_bytes(good)
    result = invoke('rollback.sh', [str(backup)])
    assert b'ROLLBACK OK' in result.stdout
    pre_unchanged()
    assert (state / 'LCS_ROBUST_SYNC').read_text() == '1\n'
    print('PASS rollback: hostname/manual-edit guards, PREIMAGE restoration under lock; robust mode stays ON')
    # A crash between the two replacements is recoverable with the same archive.
    (base / 'tools/lane_code_filter.py').write_bytes((package / 'tools/lane_code_filter.py').read_bytes())
    invoke('rollback.sh', [str(backup)]); pre_unchanged()
    print('PASS rollback restores a partial two-file installation')
    print('ALL INSTALL TESTS PASSED on Python ' + sys.version.split()[0])


if __name__ == '__main__':
    main()
