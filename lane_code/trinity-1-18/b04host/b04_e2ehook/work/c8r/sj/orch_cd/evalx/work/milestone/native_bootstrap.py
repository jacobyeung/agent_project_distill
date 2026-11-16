import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import runpy
import sys


SCHEMA = 'evalx-native-runtime-v1'
ARCHIVE = 'ffc81db4b3b1c3d1e42ac91159d504dc57b36eebfc75f537d15a426bbe6a8a22'
SOURCE = 'b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'
IMPORTS = ('numpy', 'scipy', 'torch', 'transformers', 'triton', 'fla', 'PIL')
ROLES = ('fla', 'numpy', 'kit', 'anyhost', 'aliases')
REQUIRED_OVERLAYS = {'numpy': 'numpy', 'fla': 'fla', 'triton': 'fla'}
REQUIRED_VERSIONS = {'fla': '0.6.0', 'triton': '3.7.1'}


def checked(pin):
    path = Path(pin['path'])
    if not path.is_absolute() or not path.is_file():
        raise ValueError('Runtime pin must identify a staged file')
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != pin['sha256']:
        raise ValueError('Native runtime file hash differs: '+str(path))
    return path


def configure(spec):
    if not sys.flags.isolated or not sys.dont_write_bytecode or os.environ.get('PYTHONPATH'):
        raise ValueError('Native workers require isolated Python, disabled bytecode and no PYTHONPATH')
    if (spec.get('schema') != SCHEMA or spec.get('runtime_archive_sha256') != ARCHIVE
            or spec.get('source_map_sha256') != SOURCE):
        raise ValueError('Native runtime/source identity differs')
    if checked(spec['python']).resolve() != Path(sys.executable).resolve():
        raise ValueError('Native interpreter differs')
    paths = [Path(spec['import_paths'][name]) for name in ROLES]
    if any(not p.is_absolute() or not p.is_dir() for p in paths) or len(set(paths)) != len(paths):
        raise ValueError('Native import overlay paths are missing or ambiguous')
    if set(spec['imports']) != set(IMPORTS):
        raise ValueError('Native import pin set differs')
    if any(name in sys.modules for name in IMPORTS):
        raise ValueError('A native dependency was imported before overlay admission')
    sys.path[:0] = [str(p) for p in paths]
    site = paths[-1]/'sitecustomize.py'
    if site.exists():
        if checked(spec['sitecustomize']).resolve() != site.resolve():
            raise ValueError('Native site customization differs')
        runpy.run_path(str(site), run_name='evalx_native_sitecustomize')
    elif spec.get('sitecustomize') is not None:
        raise ValueError('Declared native site customization is absent')
    os.environ['C1_EXPECT_FLA'] = '1'
    evidence = {}
    for name in IMPORTS:
        expected = checked(spec['imports'][name])
        if name in REQUIRED_OVERLAYS:
            root = Path(spec['import_paths'][REQUIRED_OVERLAYS[name]]).resolve()
            if not expected.resolve().is_relative_to(root):
                raise ValueError('Native dependency is outside its required overlay: '+name)
        value = importlib.import_module(name)
        if Path(value.__file__).resolve() != expected.resolve():
            raise ValueError('Native dependency resolved outside its pinned overlay: '+name)
        if name in REQUIRED_VERSIONS and getattr(value, '__version__', None) != REQUIRED_VERSIONS[name]:
            raise ValueError('Native dependency version differs: '+name)
        evidence[name] = dict(path=str(expected), sha256=spec['imports'][name]['sha256'],
                              version=getattr(value, '__version__', None))
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', required=True)
    parser.add_argument('--imports-only', action='store_true')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text())
    evidence = configure(spec)
    print(json.dumps(dict(event='native_imports_verified', imports=evidence)), flush=True)
    if args.imports_only:
        return
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        raise ValueError('A pinned native entrypoint is required')
    target = Path(command[0])
    if target.name not in spec['entrypoints'] or checked(spec['entrypoints'][target.name]).resolve() != target.resolve():
        raise ValueError('Native entrypoint differs')
    sys.argv = command
    runpy.run_path(str(target), run_name='__main__')


if __name__ == '__main__':
    main()
