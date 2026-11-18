"""Emit standalone operator scripts; execution on Orchard belongs to the operator."""
import base64
from pathlib import Path

W = Path(__file__).resolve().parent
common = '''import hashlib
import os
from pathlib import Path
import stat
import sys
import uuid

KH = Path('/project/community/jjyeung/okh7/x_69d2930d')
BACK = Path('/project/community/jjyeung/okh7/auth_x69')
LIVE = KH / 'k/4.json'
OLD = '2f450bfaa65e6ae0dcfbd1c790fdeb374b9356a9d2b48f5f4ba9835f127d2353'
NEW = 'a9fbd4e28f029d498e04d1bd943bd56454e143a66b846470e83dc2bd07961ed3'
os.umask(0o077)

def require(ok, message):
    if not ok:
        raise SystemExit('REFUSED: ' + message)

def directory(path):
    require(path.is_dir() and not path.is_symlink(), 'directory missing or symlink: ' + str(path))

def verified(path, want):
    require(not path.is_symlink() and path.is_file(), 'regular file required: ' + str(path))
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == want, 'sha256 differs: ' + str(path))
    return data

def absent(path):
    require(not os.path.lexists(path), 'destination exists: ' + str(path))

def write_new(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    require(stat.S_IMODE(path.stat().st_mode) == 0o600, 'file mode differs')

def syncdir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def rename_absent(source, destination):
    # Operator runs once with no competing writers. Ordinary rename uses flags=0;
    # /project rejects renameat2 flags. Preserve every displaced file outside k/.
    absent(destination)
    os.rename(source, destination)
    syncdir(destination.parent)
    if source.parent != destination.parent:
        syncdir(source.parent)

directory(KH.parent)
directory(KH)
directory(KH / 'k')
'''
install = common + '''require(len(sys.argv) == 1, 'install takes no arguments')
import base64
payload = base64.b64decode(PAYLOAD)
require(hashlib.sha256(payload).hexdigest() == NEW, 'embedded payload differs')
original = verified(LIVE, OLD)
absent(BACK)
os.mkdir(BACK, 0o700)
require(stat.S_IMODE(BACK.stat().st_mode) == 0o700, 'backup directory mode differs')
backup = BACK / '4.p.json'
write_new(backup, original)
verified(backup, OLD)
syncdir(BACK)
temporary = KH / ('.4.train.171377.' + uuid.uuid4().hex + '.tmp')
write_new(temporary, payload)
verified(temporary, NEW)
verified(LIVE, OLD)
displaced = BACK / '4.displaced.p.json'
rename_absent(LIVE, displaced)
# A failure from here leaves the original in BACK and the new bytes in temporary.
# Stop and inspect; do not rerun install or silently overwrite a competing file.
rename_absent(temporary, LIVE)
verified(LIVE, NEW)
print(OLD + '  ' + str(backup))
print(NEW + '  ' + str(LIVE))
print('INSTALLED 171377; restore after all four workers pass authorize, before the CPU inventory check.')
'''
install = install.replace('PAYLOAD', repr(base64.b64encode((W/'4.train.json').read_bytes()).decode()))
restore = common + '''require(sys.argv[1:] == ['--all-workers-authorized-171377'],
        'usage: bash restore.sh --all-workers-authorized-171377; use only after all four workers pass authorize')
directory(BACK)
require(stat.S_IMODE(BACK.stat().st_mode) == 0o700, 'backup directory mode differs')
original = verified(BACK / '4.p.json', OLD)
verified(LIVE, NEW)
saved = BACK / '4.train.json'
absent(saved)
# An exclusive marker serializes a single restore; failures require inspection.
write_new(BACK / 'restore.started', b'171377\\n')
temporary = KH / ('.4.restore.171377.' + uuid.uuid4().hex + '.tmp')
write_new(temporary, original)
verified(temporary, OLD)
verified(LIVE, NEW)
rename_absent(LIVE, saved)
rename_absent(temporary, LIVE)
verified(LIVE, OLD)
require(stat.S_IMODE(LIVE.stat().st_mode) == 0o600, 'restored file mode differs')
print(NEW + '  ' + str(saved))
print(OLD + '  ' + str(LIVE))
print('RESTORED 171377; original bytes restored; no auxiliary files were written into k/.')
'''
for name, body in [('install.sh', install), ('restore.sh', restore)]:
    script = '#!/bin/bash\nset -euo pipefail\numask 077\n# Orchard operator only; run once, with no competing authority writer.\n'
    script += '/usr/bin/python3 -I - "$@" <<\'PY_AUTH\'\n' + body + '\nPY_AUTH\n'
    (W/name).write_text(script)
    (W/name).chmod(0o700)
print('Wrote standalone install.sh and restore.sh; embedded payload sha256 pinned.')
