P=/project/community/jjyeung/okh7/a15_cot_apc82f06ad913e4
D=/project/community/jjyeung/okh7/adc82f06ad913e4/0.tgz
/usr/bin/python3 -I -s -B - "$D" "$P" <<'PYPLACE'
import hashlib, json, sys, tarfile
from pathlib import Path, PurePosixPath
src, dest = map(Path, sys.argv[1:])
assert src.stat().st_size == 4233851
assert hashlib.sha256(src.read_bytes()).hexdigest() == '40dbfa9ec987fe9f9e26d3e35143adf469f87f4860e4741ebe1187f71cfd4297'
dest.mkdir(mode=0o700)
with tarfile.open(src) as archive:
    seen = set(); total = 0
    for entry in archive:
        rel = PurePosixPath(entry.name)
        assert entry.isfile() and not rel.is_absolute() and '..' not in rel.parts
        assert entry.name not in seen
        seen.add(entry.name); total += entry.size
        assert total <= 32*1024**2
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

P=/project/community/jjyeung/okh7/a15_cot_apc82f06ad913e4
/usr/bin/python3 -I -s -B "$P/3.py" cpu

P=/project/community/jjyeung/okh7/a15_cot_apc82f06ad913e4
/usr/bin/python3 -I -s -B "$P/3.py" submit

P=/project/community/jjyeung/okh7/a15_cot_apc82f06ad913e4
R=/project/community/jjyeung/okh7/afc82f06ad913e4
/usr/bin/python3 -I -s -B "$P/3.py" fetch "$R"

nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B score.py out/return.tgz --out out/call_rates.json

nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B build.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_probe.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_fixes.py
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B finish.py
