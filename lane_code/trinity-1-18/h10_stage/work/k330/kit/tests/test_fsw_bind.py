"""Check namespace sources after the actual post-stage block, without bwrap."""
import ast
import hashlib
import json
from pathlib import Path
import tarfile
from types import SimpleNamespace

import pytest

from orchard_h10.common import write

K = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('job_source', ['source', 'payload'])
def test_namespace_bind_sources_exist(tmp_path, monkeypatch, job_source):
    with tarfile.open(K/'orchard_h10/package/0.tgz') as archive:
        cfg = json.load(archive.extractfile('9.json'))
        vendor_name = 'orchard_h10/vendor/orchard_job.py'
        vendor = archive.extractfile(vendor_name).read()
        assert hashlib.sha256(vendor).hexdigest() == cfg['payload_pins'][vendor_name]['sha256']
        raw = archive.extractfile('orchard_h10/job.py').read()
    if job_source == 'source':
        raw = (K/'orchard_h10/job.py').read_bytes()

    # Execute the pinned namespace and environment functions without importing
    # unrelated vendor launch, storage, or process-control helpers.
    vendor_ast = ast.parse(vendor)
    selected = [node for node in vendor_ast.body if
                (isinstance(node, ast.FunctionDef) and node.name in ('namespace', 'environment')) or
                (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and
                 t.id in ('SJ', 'FSW', 'AP', 'UV') for t in node.targets))]
    import os
    vendor_scope = {'Path': Path, 'os': os}
    exec(compile(ast.Module(body=selected, type_ignores=[]), vendor_name, 'exec'), vendor_scope)
    J = SimpleNamespace(**vendor_scope)

    root = tmp_path/'root'
    (root/'sj').mkdir(parents=True)
    (root/'m/ap').mkdir(parents=True)
    (root/'bwrap').write_bytes(b'placeholder')
    # Runtime archive group 0 supplies this ro-bind source; staging creates it.
    (root/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu').mkdir(parents=True)
    assert not (root/'fsw').exists()
    monkeypatch.setenv('SLURM_JOB_ID', '170620')
    monkeypatch.setenv('USER', 'jjyeung')

    main = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    body = next(n for n in main.body if isinstance(n, ast.Try)).body
    start = next(i for i, n in enumerate(body) if isinstance(n, ast.Expr) and
                 isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and
                 n.value.func.id == 'stage') + 1
    end = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign) and
               isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and
               n.value.func.attr == 'environment') + 1
    assert start < end
    scope = dict(root=root, inputs={}, cfg={'stop_margin': 0}, out=root,
                 end=100, time=SimpleNamespace(time=lambda: 0), write=write, J=J)
    exec(compile(ast.Module(body=body[start:end], type_ignores=[]), 'job.py', 'exec'), scope)

    argv = J.namespace(root)
    sources = [Path(argv[i+1]) for i, arg in enumerate(argv) if arg in ('--bind', '--ro-bind')]
    assert {root/'sj', root/'fsw', root/'m/ap'} <= set(sources)
    assert all(source.exists() for source in sources), [str(p) for p in sources if not p.exists()]
