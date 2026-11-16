"""Seal the relative source bundle and every archived file's identity."""
from pathlib import Path
import hashlib
import json
import gzip
from .paths import ROOT
from .io import dump,sha,tar_bytes


def package(staging):
    staging=Path(staging)
    if not staging.is_relative_to(Path("/dev/shm/b07_n6")):raise ValueError("build staging must be in RAM")
    staging.mkdir(parents=True,exist_ok=False)
    from .portable import sources,ROOTS
    files,dependencies=sources()
    local=[ROOT/'native_read.py']+sorted((ROOT/'kit/tests').glob('*.py'))
    local += [ROOT/n for n in ('RUN.md','SIZING.md','DIFF.md','OPEN_INPUTS.md')]
    local += [ROOT/'out'/n for n in ('OPEN_INPUTS.md','MODULE_MAP.md','ORCHARD_ONLY.md',
        'N5_VALIDATION.json','N4_MEDIA_EVIDENCE.json','N4_SHARD_PLAN.json','N5_REVIEW_ORIGINAL.json')]
    for p in local:files[str(p.relative_to(ROOT))]=p.read_bytes()
    files['r.json']=json.dumps(ROOTS,sort_keys=True,indent=2).encode()+b'\n'
    from .opacity import pack,path_name,scan_members
    files['xnames.py']=(ROOT/'offnative/opacity.py').read_bytes()
    names={path_name(n):n for n in files}
    files,archive_pins=pack(files)
    files['out/ARCHIVE_TRANSPORT.json']=json.dumps(archive_pins,sort_keys=True).encode()
    dump(ROOT/'out/N5_MEMBER_MAP.json',names)
    raw=gzip.compress(tar_bytes(files),mtime=0)
    scan_members(raw)
    staged=staging/'code.tar';staged.write_bytes(raw)
    archive=ROOT/'out/code.tar'
    if archive.exists():
        previous=archive.with_name('code.before_n5.'+sha(archive)[:12]+'.tar')
        if previous.exists():raise ValueError('previous archive already retained')
        archive.rename(previous)
    archive.write_bytes(staged.read_bytes())
    pins=[dict(path=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
          for name,data in sorted(files.items())]
    dump(ROOT/'out/DEPENDENCY_PINS.json',dict(read_only=True,
        files=[r for r in dependencies['entries'] if r['logical_path'].startswith('d/')],
        staged_roots=ROOTS))
    dump(ROOT/'out/CODE_PINS.json',dict(archive=dict(path='out/code.tar',sha256=sha(archive),bytes=len(raw)),
        name_map_sha256=sha(ROOT/'out/NAME_MAP.json'),token_table_sha256=hashlib.sha256(files['x0.json']).hexdigest(),
        scope='Relative source bundle; model, media, environment, and owner artifacts are not included.',
        files=pins))
    return sha(archive)

if __name__=='__main__':
    import sys
    print(package(sys.argv[1]))
