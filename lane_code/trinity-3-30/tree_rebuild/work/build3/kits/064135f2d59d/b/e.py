"""Authenticate and unpack the source closure, then enter its production dispatcher."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import tarfile


def stage(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError('Source destination must be empty and new')
    seal = json.loads((root/'k/7.json').read_text())
    pin = seal['archive']
    source = root/pin['path']
    if hashlib.sha256(source.read_bytes()).hexdigest() != pin['sha256']:
        raise ValueError('Source archive sha256 differs')
    with tarfile.open(source) as archive:
        entries = archive.getmembers()
        if ({m.name for m in entries} != set(seal['files']) or len(entries) != len(seal['files'])
                or any(not m.isfile() or Path(m.name).is_absolute() or '..' in Path(m.name).parts
                       or m.size > 16_000_000 for m in entries)):
            raise ValueError('Source archive inventory differs')
        destination.mkdir(parents=True)
        for member in entries:
            raw = archive.extractfile(member).read()
            if hashlib.sha256(raw).hexdigest() != seal['files'][member.name]:
                raise ValueError('Source member sha256 differs')
            target = destination/member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    return destination


def main(root, mode, destination):
    root = Path(root).resolve()
    sys.path.insert(0, str(root/'b'))
    for name in ('v','a'):
        spec = importlib.util.spec_from_file_location(name, root/'b'/(name+'.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    a = sys.modules['a']
    a.main(root, build_only=True)
    source = stage(root, destination)
    sys.path.insert(0, str(source))
    from student_pilot.source_seal import check_archive
    seal = json.loads((root/'k/7.json').read_text())
    check_archive({**seal['archive'], 'path': str(root/seal['archive']['path'])}, seal['files'])
    module = importlib.import_module('launch_r2.entry')
    return module.main(root, mode)


if __name__ == '__main__':
    main(*sys.argv[1:])
