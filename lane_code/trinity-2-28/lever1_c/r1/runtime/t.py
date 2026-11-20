"""Pinned input and process-local state contracts."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path


def assert_reader_root(root):
    import sys
    root=Path(root).resolve()
    for key,module in tuple(sys.modules.items()):
        if key=='e2e_reader' or key.startswith('e2e_reader.'):
            source=getattr(module,'__file__',None)
            if not source or not Path(source).resolve().is_relative_to(root):raise ImportError('E11')


def bind_reader_root(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]/'b').resolve()
    if not (root/'e2e_reader').is_dir():raise ImportError('E12')
    assert_reader_root(root)
    return root


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def load_rows():
    here=Path(__file__).parent
    pins=json.loads((here/'1.json').read_text())
    if sha(here/'0.json')!=pins['0']:raise ValueError('E13')
    rows=json.loads((here/'0.json').read_text())['items']
    if len(rows)!=150 or len({r['item_id'] for r in rows})!=150:raise ValueError('E14')
    return rows


def capture_path(config):
    out=Path(config['output']).resolve()
    path=Path(config.get('capture',out.parent/'c/0.gz')).resolve()
    if path!=out.parent/'c/0.gz' or path==out or out in path.parents or str(path).startswith('/project/'):
        raise ValueError('E15')
    return path


@contextmanager
def fresh_perception(gen):
    memo=getattr(gen.perception,'memo',None)
    if memo is None:yield;return
    modules=memo.modules;memo.modules=frozenset()
    try:yield
    finally:memo.modules=modules
