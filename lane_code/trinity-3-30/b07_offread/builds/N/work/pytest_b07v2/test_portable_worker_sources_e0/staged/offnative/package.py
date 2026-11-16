"""Seal the relative source bundle and every archived file's identity."""
from pathlib import Path
import hashlib
import json
from .paths import ROOT
from .io import dump,sha,tar_bytes


def package():
    from .portable import sources,ROOTS
    files,dependencies=sources()
    local=[ROOT/'native_read.py']+sorted((ROOT/'kit/tests').glob('*.py'))
    local += [ROOT/n for n in ('RUN.md','SIZING.md','DIFF.md')]
    for p in local:files[str(p.relative_to(ROOT))]=p.read_bytes()
    files['r.json']=json.dumps(ROOTS,sort_keys=True,indent=2).encode()+b'\n'
    raw=tar_bytes(files)
    archive=ROOT/'out/code.tar';archive.write_bytes(raw)
    pins=[dict(path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
          for name,data in sorted(files.items())]
    dump(ROOT/'out/DEPENDENCY_PINS.json',dict(read_only=True,
        files=[r for r in dependencies['entries'] if r['logical_path'].startswith('d/')],
        staged_roots=ROOTS))
    dump(ROOT/'out/CODE_PINS.json',dict(archive=dict(path='out/code.tar',sha256=sha(archive),bytes=len(raw)),
        scope='Relative source bundle; model, media, environment, and owner artifacts are not included.',
        files=pins))
    return sha(archive)

if __name__=='__main__':print(package())
