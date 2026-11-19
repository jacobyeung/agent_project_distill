#!/bin/bash
# Saved owner script: bash -eu /path/to/so_syncfix/rollback.sh /absolute/install-backups/<id>
# The sourced disable retains .sync.lock until this shell exits.
source "$(dirname "${BASH_SOURCE[0]}")/disable.sh" "$@"
RESTORE=$(mktemp -d "$S/tmp_rollback-$STAMP-XXXXXX")
printf 'RESTORE_DIRECTORY %s\n' "$RESTORE"
# Cluster rules require extraction on scratch, never directly into /data*.
printf 'RESTORE: tar xf %q -C %q\n' "$BACKUP/preimage.tar" "$RESTORE"
nice -n 10 tar xf "$BACKUP/preimage.tar" -C "$RESTORE"
(cd "$RESTORE" && nice -n 10 sha256sum -c "$BACKUP/PREIMAGE.sha256")
nice -n 10 "$PYTHON" -I -s -B - "$RESTORE" "$B" "$BACKUP/PREIMAGE.sha256" "$STAMP" <<'PY'
import hashlib
import os
from pathlib import Path
import sys
source, base, manifest = [Path(value) for value in sys.argv[1:4]]
pending = []
for line in manifest.read_text().splitlines():
    digest, name = line.split(None, 1)
    if not name.startswith('tools/') or len(Path(name).parts) != 2:
        raise ValueError('unexpected backup path: ' + name)
    data = (source / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('backup checksum mismatch: ' + name)
    destination = base / name
    temporary = destination.with_name('.' + destination.name + '.rollback-' + sys.argv[4])
    print('ROLLBACK_PENDING ' + str(temporary), flush=True)
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod((source / name).stat().st_mode & 0o777)
    pending.append((temporary, destination))
for temporary, destination in sorted(pending, key=lambda pair: pair[1].name == 'lane_code_sync.sh'):
    os.replace(str(temporary), str(destination))
PY
(cd "$B" && nice -n 10 sha256sum -c "$BACKUP/PREIMAGE.sha256")
echo 'ROLLBACK OK: preimage verified; robust mode is OFF; unused robust helpers and retired stage remain retained.'
date -u
