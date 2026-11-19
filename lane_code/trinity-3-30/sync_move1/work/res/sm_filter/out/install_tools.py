"""Install or roll back the two validated tools under the hourly sync lock (Python 3.6)."""
import fcntl
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
import uuid

NAMES = ('tools/lane_code_filter.py', 'tools/dry_count.py')


def manifest(path):
    result = {}
    for line in path.read_text().splitlines():
        expected, name = line.split(None, 1)
        name = name.strip()
        if name not in NAMES or name in result or len(expected) != 64:
            raise ValueError('unexpected manifest entry: ' + name)
        int(expected, 16)
        result[name] = expected
    if set(result) != set(NAMES):
        raise ValueError('manifest must name exactly the two replacement tools')
    return result


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_tool(root, name):
    path = root / name
    if path.is_symlink() or not path.is_file():
        raise ValueError('not a regular non-symlink tool: ' + str(path))
    return path.read_bytes()


def hashes(root, expected):
    for name in NAMES:
        if digest(read_tool(root, name)) != expected[name]:
            raise ValueError('preimage/postimage mismatch: ' + str(root / name))
        print(name + ': OK', flush=True)


def package_hashes(package):
    # Reject absolute/traversing paths before asking sha256sum to read any file.
    entries = set()
    for line in (package / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split(None, 1)
        name = name.strip()
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or name in entries or name == 'SHA256SUMS':
            raise ValueError('unsafe/duplicate package checksum entry: ' + name)
        if (package / path).is_symlink() or not (package / path).is_file():
            raise ValueError('package member is not a regular file: ' + name)
        entries.add(name)
    required = set(NAMES) | {'PREIMAGE.sha256', 'POSTIMAGE.sha256', 'install.sh', 'rollback.sh', 'install_tools.py'}
    if not required <= entries:
        raise ValueError('package checksums omit required files')
    subprocess.check_call(['sha256sum', '-c', 'SHA256SUMS'], cwd=str(package))


def stage(base, data, token, names):
    pending = []
    for name in names:
        destination = base / name
        if destination.is_symlink() or not destination.is_file():
            raise ValueError('destination must be an existing regular tool: ' + str(destination))
        temporary = destination.parent / ('.' + destination.name + '.lcs-' + token)
        print('INSTALL_PENDING ' + str(temporary), flush=True)
        mode = stat.S_IMODE(destination.stat().st_mode)
        fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
        with os.fdopen(fd, 'wb') as target:
            target.write(data[name])
            target.flush()
            os.fchmod(target.fileno(), mode)
            os.fsync(target.fileno())
        if name.endswith('.sh'):
            subprocess.check_call(['bash', '-n', str(temporary)])
        else:
            compile(temporary.read_bytes(), str(temporary), 'exec')
        pending.append((temporary, destination))
    return pending


def replace(pending):
    for temporary, destination in pending:
        os.replace(str(temporary), str(destination))
        print('INSTALLED ' + str(destination), flush=True)
    # Persist directory entries as well as the completed temporary files.
    fd = os.open(str(pending[0][1].parent), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def install(package, base, state):
    pre = manifest(package / 'PREIMAGE.sha256')
    post = manifest(package / 'POSTIMAGE.sha256')
    hashes(base, pre)
    hashes(package, post)
    token = uuid.uuid4().hex
    backup = state / 'install-backups' / token
    backup.mkdir(parents=True)
    archive = backup / 'preimage.tar'
    with tarfile.open(str(archive), 'w') as stream:
        for name in NAMES:
            stream.add(str(base / name), arcname=name, recursive=False)
    (backup / 'PREIMAGE.sha256').write_bytes((package / 'PREIMAGE.sha256').read_bytes())
    # Verify the archive before replacing any installed byte.
    backup_data(backup, pre)
    print('BACKUP ' + str(backup), flush=True)
    data = {name: read_tool(package, name) for name in NAMES}
    pending = stage(base, data, token, NAMES)
    hashes(base, pre)
    replace(pending)
    hashes(base, post)
    print('INSTALL OK; robust mode remains unchanged.', flush=True)


def backup_data(backup, pre):
    result = {}
    with tarfile.open(str(backup / 'preimage.tar'), 'r:') as stream:
        for member in stream.getmembers():
            if member.name not in NAMES or member.name in result or not member.isfile() or member.size > 2 * 1024 * 1024:
                raise ValueError('unexpected preimage archive member: ' + member.name)
            result[member.name] = stream.extractfile(member).read()
    if set(result) != set(pre) or any(digest(result[name]) != pre[name] for name in pre):
        raise ValueError('preimage archive checksum mismatch')
    return result


def rollback(package, base, state, backup):
    backup.relative_to(state / 'install-backups')
    pre = manifest(backup / 'PREIMAGE.sha256')
    if pre != manifest(package / 'PREIMAGE.sha256'):
        raise ValueError('backup belongs to a different preimage')
    data = backup_data(backup, pre)
    post = manifest(package / 'POSTIMAGE.sha256')
    # Accept a partial install, but never overwrite unrelated manual edits.
    def check_current():
        for name in NAMES:
            if digest(read_tool(base, name)) not in (pre[name], post[name]):
                raise ValueError('installed tool differs from both package images: ' + name)
    check_current()
    pending = stage(base, data, uuid.uuid4().hex, tuple(reversed(NAMES)))
    check_current()
    replace(pending)
    hashes(base, pre)
    print('ROLLBACK OK; robust mode remains unchanged.', flush=True)


def main():
    action = sys.argv[1]
    package, base, state = [Path(p).resolve() for p in sys.argv[2:5]]
    if subprocess.check_output(['hostname', '-s']).strip() != b'trinity-3-30':
        raise ValueError('install/rollback only on trinity-3-30')
    # LOCK_NB is the same nonblocking exclusive operation as flock -n.
    with open(str(state / '.sync.lock'), 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('An existing sync holds the lock; installation/rollback deferred.', flush=True)
            return 3
        package_hashes(package)
        if action == 'install' and len(sys.argv) == 5:
            install(package, base, state)
        elif action == 'rollback' and len(sys.argv) == 6:
            rollback(package, base, state, Path(sys.argv[5]).resolve())
        else:
            raise ValueError('expected install or rollback with one backup directory')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('INSTALL/ROLLBACK FAILED: %s; retain the logged backup and temporary paths.' % error, file=sys.stderr)
        sys.exit(2)
