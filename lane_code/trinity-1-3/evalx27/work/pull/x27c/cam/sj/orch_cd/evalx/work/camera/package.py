import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parent
FILES = ('direct.py', 'report_camera.py', 'run_camera.sh', 'runtime.py', 'package.py', 'models.json',
         'vendor/r3/adapter.py', 'vendor/r4/adapter.py', 'vendor/r5/adapter.py',
         'vendor/r5/dev_scoring.py', 'vendor/r5/report.py', 'vnice/vnice.sh', 'vnice/terminator.sh')
PREFIX = 'sj/orch_cd/evalx/work/camera/'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(root):
    root = Path(root)
    pins = json.loads((root/'PACKAGE.json').read_text())
    for name, record in pins['files'].items():
        path = root/name
        if path.resolve().parent != root.resolve() and root.resolve() not in path.resolve().parents:
            raise ValueError('Package member escapes root')
        raw = path.read_bytes()
        if sha(raw) != record['sha256'] or len(raw) != record['bytes']:
            raise ValueError('Package member changed: '+name)
    print(json.dumps(dict(package='VERIFIED', files=len(pins['files']))))


def make(dest):
    dest = Path(dest)
    if dest.exists():
        raise ValueError('Package destination exists')
    names = list(FILES)+['payload/'+p.name for p in sorted((ROOT/'payload').iterdir()) if p.is_file()]
    data = {name:(ROOT/name).read_bytes() for name in names}
    if sum(map(len, data.values())) > 100*1024**2:
        raise ValueError('Camera package exceeds its 100 MiB limit')
    pins = dict(schema='camera-direct-package-v1',
                files={name:dict(sha256=sha(raw), bytes=len(raw)) for name,raw in sorted(data.items())})
    manifest = (json.dumps(pins, indent=2, sort_keys=True)+'\n').encode()
    (ROOT/'PACKAGE.json').write_bytes(manifest)
    data['PACKAGE.json'] = manifest
    with tarfile.open(dest, 'w') as archive:
        for name, raw in sorted(data.items()):
            info = tarfile.TarInfo(PREFIX+name)
            info.size = len(raw)
            info.mode = 0o555 if name.endswith('.sh') else 0o444
            archive.addfile(info, io.BytesIO(raw))
    receipt = dict(path=str(dest.resolve()), bytes=dest.stat().st_size, sha256=sha(dest.read_bytes()),
                   package_sha256=sha(manifest))
    with (dest.with_suffix('.json')).open('x') as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    verify(ROOT)
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--make')
    group.add_argument('--verify')
    args = parser.parse_args()
    make(args.make) if args.make else verify(args.verify)
