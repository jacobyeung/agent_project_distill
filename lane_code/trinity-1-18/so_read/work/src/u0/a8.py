"""Explicit extension loader. The original entrypoints never import this file."""
import argparse
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
MODULES = (
    ('e2e_reader.read_cache', 'a0.py'),
    ('e2e_reader.stage1', 'a3.py'),
    ('e2e_reader.real', 'a2.py'),
    ('e2e_reader.parity', 'a1.py'),
    ('h1eval.h10.atomic_journal', 'a5.py'),
    ('h1eval.h10.launch', 'a4.py'),
    ('h1eval.h10.merge_read', 'a6.py'),
    ('h1eval.h10.array_worker', 'a7.py'),
)
_active = False


def source_hash():
    h = hashlib.sha256()
    for path in sorted(ROOT.glob('a*.py')):
        h.update(path.name.encode()); h.update(path.read_bytes())
    return h.hexdigest()


def activate(*, enabled=False):
    global _active
    if enabled is not True:
        raise ValueError('Extensions are OFF; explicit enabled=True is required')
    if _active:
        return
    for name, filename in MODULES:
        parent, _, leaf = name.rpartition('.')
        package = importlib.import_module(parent)
        spec = importlib.util.spec_from_file_location(name, ROOT/filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        setattr(package, leaf, module)
        spec.loader.exec_module(module)
    _active = True


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--enable-extensions', action='store_true')
    args, rest = parser.parse_known_args(argv)
    if not args.enable_extensions:
        parser.error('Extensions are OFF; pass --enable-extensions')
    source = ROOT.parent
    sys.path[:0] = [str(source), str(source/'tree'), str(source/'b')]
    if '--opaque' in rest:
        from a9 import install_wire_decoder,PublicLog
        install_wire_decoder()
        sys.stdout=PublicLog(sys.stdout);sys.stderr=PublicLog(sys.stderr)
    activate(enabled=True)
    from h1eval.h10.launch import main as launch
    return launch(rest)


if __name__ == '__main__':
    raise SystemExit(main())
