"""Install validated tools under the existing lock; retain a preimage archive and log every temporary path."""
import fcntl
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
import uuid


def hashes(root, manifest):
    result = {}
    for line in manifest.read_text().splitlines():
        expected, name = line.split(None, 1)
        name = name.strip()
        if not name.startswith('tools/') or len(Path(name).parts) != 2:
            raise ValueError('unexpected manifest path: ' + name)
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('not a regular non-symlink tool: ' + str(path))
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('preimage/postimage mismatch: ' + str(path))
        result[name] = expected
        print(name + ': OK', flush=True)
    return result


def main():
    package, base, state = [Path(p).resolve() for p in sys.argv[1:4]]
    if subprocess.check_output(['hostname', '-s']).strip() != b'trinity-3-30':
        raise ValueError('install only on trinity-3-30')
    with open(str(state / '.sync.lock'), 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('An existing sync holds the lock; installation deferred.', flush=True)
            return 3
        flag = state / 'LCS_ROBUST_SYNC'
        if os.environ.get('LCS_ROBUST_SYNC') == '1' or (flag.is_file() and not flag.is_symlink()):
            raise ValueError('robust mode must be OFF during initial installation')
        pre = hashes(base, package / 'PREIMAGE.sha256')
        hashes(package, package / 'POSTIMAGE.sha256')
        for name in ('lane_code_stage.sh', 'lane_code_log.py'):
            helper = base / 'tools' / name
            if helper.exists() or helper.is_symlink():
                raise ValueError('new helper already exists; reconcile before installation: ' + name)
        subprocess.check_call([sys.executable, '-I', '-s', '-B', str(package / 'tools' / 'lane_code_log.py'),
                               str(state / 'install-preflight.log'), '-', '0', '/bin/true'])
        print('PREFLIGHT bounded regular log: OK', flush=True)
        token = uuid.uuid4().hex
        backup = state / 'install-backups' / token
        backup.mkdir(parents=True)
        archive = backup / 'preimage.tar'
        with tarfile.open(str(archive), 'w') as stream:
            for name in sorted(pre):
                stream.add(str(base / name), arcname=name, recursive=False)
        (backup / 'PREIMAGE.sha256').write_bytes((package / 'PREIMAGE.sha256').read_bytes())
        print('BACKUP ' + str(archive), flush=True)
        # Stage every complete file before replacing any installed file. The driver is last.
        names = ['lane_code_log.py', 'lane_code_filter.py', 'lane_code_scan.py', 'tssh.sh', 'lane_code_stage.sh', 'lane_code_sync.sh']
        pending = []
        for name in names:
            destination = base / 'tools' / name
            temporary = base / 'tools' / ('.' + name + '.lcs-' + token)
            print('INSTALL_PENDING ' + str(temporary), flush=True)
            mode = stat.S_IMODE(destination.stat().st_mode) if destination.exists() else 0o755
            fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
            with os.fdopen(fd, 'wb') as target:
                target.write((package / 'tools' / name).read_bytes())
                target.flush()
                os.fsync(target.fileno())
            if name.endswith('.sh'):
                subprocess.check_call(['bash', '-n', str(temporary)])
            else:
                compile(temporary.read_bytes(), str(temporary), 'exec')
            pending.append((temporary, destination))
        hashes(base, package / 'PREIMAGE.sha256')
        for temporary, destination in pending:
            os.replace(str(temporary), str(destination))
            print('INSTALLED ' + str(destination), flush=True)
        hashes(base, package / 'POSTIMAGE.sha256')
        print('INSTALL OK; robust mode remains OFF. Calibrate before creating the flag.', flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('INSTALL FAILED: %s; retain the logged backup and temporary paths.' % error, file=sys.stderr)
        sys.exit(2)
