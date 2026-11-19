"""Build the symlink stage of N's uploads (same mapping as upload.py): python3 stage.py PKGROOT STAGE"""
import json, os, sys, hashlib
from pathlib import Path
root, stage = Path(sys.argv[1]), Path(sys.argv[2])
v = json.loads((root/'work/build21/UPLOADS.json').read_text()); rows = []
stage.mkdir()
for e in v['files']:
    n = Path(e['opaque_name']); assert not n.is_absolute() and '..' not in n.parts
    local = (root/'work/build21/kits'/n) if n.parts[0] == 'q' else root/'work/build21/upload'/n
    assert local.is_file() and local.stat().st_size == e['bytes'], n
    assert hashlib.sha256(local.read_bytes()).hexdigest() == e['sha256'], n
    t = stage/n; t.parent.mkdir(parents=True, exist_ok=True); os.symlink(local.resolve(), t)
    rows.append([str(n), e['sha256'], e['bytes']])
(stage.parent/(stage.name+'.list.json')).write_text(json.dumps(rows))
print(len(rows), v['total_bytes'])
