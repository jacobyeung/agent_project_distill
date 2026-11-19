"""Install or restore the sync-host tools under the owner's existing sync lock."""
import fcntl
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
import uuid

REPLACED = ('tools/lane_code_stage.sh', 'tools/land_kit.py', 'tools/lane_code_sync.sh')
ADDED = 'tools/lane_code_sync_loop.sh'


def manifest(path):
    result = {}
    for line in path.read_text().splitlines():
        expected, name = line.split(None, 1)
        if name not in REPLACED + (ADDED,) or name in result:
            raise ValueError('unexpected manifest path: ' + name)
        result[name] = expected
    return result


def digest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('not a regular non-symlink tool: ' + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root, entries):
    for name, expected in sorted(entries.items()):
        if digest(root / name) != expected:
            raise ValueError('preimage/postimage mismatch: ' + str(root / name))
        print(name + ': OK', flush=True)


def prepare(base, name, data, mode, token):
    destination = base / name
    temporary = destination.with_name('.' + destination.name + '.lcs-' + token)
    print('INSTALL_PENDING ' + str(temporary), flush=True)
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as target:
        os.fchmod(target.fileno(), mode)
        target.write(data)
        target.flush()
        os.fsync(target.fileno())
    if name.endswith('.sh'):
        subprocess.check_call(['bash', '-n', str(temporary)])
    else:
        compile(temporary.read_bytes(), str(temporary), 'exec')
    return temporary, destination


def publish(pending):
    for temporary, destination in pending:
        os.replace(str(temporary), str(destination))
        print('INSTALLED ' + str(destination), flush=True)


def require_absent(path):
    if path.exists() or path.is_symlink():
        raise ValueError('new helper already exists: ' + str(path))


def install(package, base, state, pre, post):
    hashes(base, pre)
    hashes(package, post)
    require_absent(base / ADDED)
    token = uuid.uuid4().hex
    backup = state / 'install-backups' / token
    backup.mkdir(parents=True)
    archive = backup / 'preimage.tar'
    with tarfile.open(str(archive), 'w') as stream:
        for name in sorted(pre):
            stream.add(str(base / name), arcname=name, recursive=False)
    (backup / 'PREIMAGE.sha256').write_bytes((package / 'PREIMAGE.sha256').read_bytes())
    print('BACKUP ' + str(backup), flush=True)
    pending = []
    # All temporaries must pass syntax checks before the first installed file changes.
    for name in REPLACED[:-1] + (ADDED,) + REPLACED[-1:]:
        mode = 0o755 if name == ADDED else stat.S_IMODE((base / name).stat().st_mode)
        pending.append(prepare(base, name, (package / name).read_bytes(), mode, token))
    hashes(base, pre)
    require_absent(base / ADDED)
    publish(pending)
    hashes(base, post)
    print('INSTALL OK; robust flag and budgets unchanged.', flush=True)


def rollback(package, base, backup, pre, post):
    if (backup / 'PREIMAGE.sha256').read_bytes() != (package / 'PREIMAGE.sha256').read_bytes():
        raise ValueError('backup PREIMAGE differs from this package')
    # Accept a complete installation or a partial sequence of pre/postimage files.
    for name in REPLACED:
        if digest(base / name) not in (pre[name], post[name]):
            raise ValueError('installed tool changed; refusing rollback: ' + name)
    added = base / ADDED
    if added.exists() or added.is_symlink():
        if digest(added) != post[ADDED]:
            raise ValueError('new helper changed; refusing rollback')
    token = uuid.uuid4().hex
    pending = []
    with tarfile.open(str(backup / 'preimage.tar'), 'r:') as stream:
        members = stream.getmembers()
        if len(members) != len(pre) or set(m.name for m in members) != set(pre):
            raise ValueError('unexpected backup archive members')
        for member in members:
            if not member.isfile():
                raise ValueError('backup member is not regular: ' + member.name)
            data = stream.extractfile(member).read()
            if hashlib.sha256(data).hexdigest() != pre[member.name]:
                raise ValueError('backup hash mismatch: ' + member.name)
            pending.append(prepare(base, member.name, data, member.mode, token))
    publish(pending)
    if added.exists():
        aside = added.with_name('.' + added.name + '.rollback-' + token)
        os.rename(str(added), str(aside))
        print('RENAMED_ASIDE ' + str(aside), flush=True)
    hashes(base, pre)
    print('ROLLBACK OK; robust flag and budgets unchanged.', flush=True)


def main():
    action = sys.argv[1]
    package, base, state = [Path(p).resolve() for p in sys.argv[2:5]]
    if subprocess.check_output(['hostname', '-s']).strip() != b'trinity-3-30':
        raise ValueError('install/rollback only on trinity-3-30')
    if (base / 'tools').is_symlink() or not (base / 'tools').is_dir():
        raise ValueError('tools must be a regular directory')
    if (state / '.sync.lock').is_symlink():
        raise ValueError('sync lock must not be a symlink')
    with open(str(state / '.sync.lock'), 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('An existing sync holds the lock; installation/rollback deferred.', flush=True)
            return 3
        subprocess.check_call(['sha256sum', '--strict', '-c', 'SHA256SUMS'], cwd=str(package))
        pre = manifest(package / 'PREIMAGE.sha256')
        post = manifest(package / 'POSTIMAGE.sha256')
        if set(pre) != set(REPLACED) or set(post) != set(REPLACED + (ADDED,)):
            raise ValueError('unexpected preimage/postimage inventory')
        if action == 'install':
            install(package, base, state, pre, post)
        elif action == 'rollback':
            rollback(package, base, Path(sys.argv[5]).resolve(), pre, post)
        else:
            raise ValueError('unknown action: ' + action)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('INSTALL/ROLLBACK FAILED: %s; retain the logged backup and temporary paths.' % error,
              file=sys.stderr)
        sys.exit(2)
