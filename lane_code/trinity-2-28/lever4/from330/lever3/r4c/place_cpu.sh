set -e
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo "project_free=${F}G $(date -u +%FT%TZ)"; [ "$F" -ge 15 ] || { echo "HOLD below 15 GiB floor"; exit 3; }
G=$(TZ=UTC squeue -u $USER -h -p general -o '%i %j'); echo "general: $G"; [ -z "$G" ] || { echo "HOLD: our job on general"; exit 5; }
P=/project/community/jjyeung/okh7/a15_cot_ap87f4ae5c2f44f
D=/project/community/jjyeung/okh7/ad87f4ae5c2f44f/0.tgz
/usr/bin/python3 -I -s -B - "$D" "$P" <<'PYPLACE'
import hashlib, json, sys, tarfile
from pathlib import Path, PurePosixPath
src, dest = map(Path, sys.argv[1:])
assert src.stat().st_size == 4309485
assert hashlib.sha256(src.read_bytes()).hexdigest() == '3998032470651ac870851f39990f638ead7efc6647e2a9c607508ecbe1400cbd'
dest.mkdir(mode=0o700)
with tarfile.open(src) as archive:
    seen = set(); total = 0
    for entry in archive:
        rel = PurePosixPath(entry.name)
        assert entry.isfile() and not rel.is_absolute() and '..' not in rel.parts
        assert entry.name not in seen
        seen.add(entry.name); total += entry.size
        assert total <= 32*1024**2 and total+src.stat().st_size <= 20000000
        target = dest/entry.name
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with target.open('xb') as output:
            output.write(archive.extractfile(entry).read())
        target.chmod(0o600)
(dest/'a').mkdir(mode=0o700)
for name, pin in json.loads((dest/'0.json').read_text())['files'].items():
    raw = (dest/name).read_bytes()
    assert len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256']
print('OK')
PYPLACE
/usr/bin/python3 -I -s -B "$P/3.py" check
/usr/bin/python3 -I -s -B "$P/3.py" cpu
echo cpu_submitted_rc=$?
