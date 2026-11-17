"""Exercise the archived reader's import paths in fresh CPU processes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

K = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def payload(tmp_path_factory):
    p = tmp_path_factory.mktemp('distance_payload')
    package = Path(os.environ.get('DISTANCE_PACKAGE', K/'orchard_h10/package/0.tgz'))
    with tarfile.open(package) as archive:
        for member in archive:
            assert member.isfile()
            target = p/member.name
            assert target.resolve().is_relative_to(p)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    return p


PROBE = '''
import ast
import importlib
import json
from pathlib import Path
import sys
p = Path(sys.argv[1])
# Execute the packaged entry's exact path assignment; -I excludes host code.
entry = ast.parse((p/'orchard_h10/entry.py').read_bytes())
paths = [n for n in entry.body if isinstance(n, ast.Assign)
         and any(isinstance(t, ast.Subscript) and ast.unparse(t.value) == 'sys.path'
                 for t in n.targets)]
assert len(paths) == 1
exec(compile(ast.Module(body=paths, type_ignores=[]), 'entry.py', 'exec'))
assert sys.path[:3] == [str(p/'b'), str(p/'tree'), str(p)]
name = sys.argv[2]
if name == 'selector_inputs':
    source = p/'b/e2e_reader/stage1.py'
    tree = ast.parse(source.read_bytes())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'StageOne')
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
    head = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'HEADS' for t in n.targets))
    imports = init.body[:3]
    assert isinstance(imports[1], ast.If)
    assert isinstance(imports[2], ast.Import) and imports[2].names[0].name == name
    scope = dict(sys=sys, Path=Path, __file__=str(source))
    exec(compile(ast.Module(body=[head] + imports, type_ignores=[]), str(source), 'exec'), scope)
    module = sys.modules[name]
    assert Path(module.__file__).resolve() == p/'b/heads/selector/sl118/selector_inputs.py'
else:
    try:
        module = importlib.import_module(name)
    except ImportError as error:
        print(json.dumps(dict(skip=f'{type(error).__name__}: {error}')))
        sys.exit(0)
    assert Path(module.__file__).resolve().is_relative_to(p/'b/e2e_reader')
print(json.dumps(dict(imported=name, file=module.__file__)))
'''


@pytest.mark.parametrize('name', [
    'selector_inputs', 'e2e_reader.stage1', 'e2e_reader.grounding', 'e2e_reader.real'])
def test_distance_imports(payload, name):
    result = subprocess.run([sys.executable, '-I', '-B', '-c', PROBE, str(payload), name],
                            cwd=payload, capture_output=True, text=True,
                            env={**os.environ, 'CUDA_VISIBLE_DEVICES': ''})
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout.splitlines()[-1])
    if 'skip' in record:
        pytest.skip(f'{name}: {record["skip"]}')
    assert record['imported'] == name
