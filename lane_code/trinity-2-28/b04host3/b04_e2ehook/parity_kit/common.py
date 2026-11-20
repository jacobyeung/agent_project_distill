"""Small local metadata operations shared by the parity commands."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

LANE = Path(__file__).resolve().parents[1]
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449')
C8R = LANE / 'work/c8r/sj/orch_cd/evalx/work/milestone/native/out2'
META = LANE / 'work/meta/x'
PREP = Path('fsw/ap/8865619b/runs/469ddece/inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd')
TASKS = [META / 'sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl',
         META / 'sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl']
FRAMES = META / 'sj/orch_cd/legs1_reads/work/vendor/r3/FRAMES.json'
DENSE = META / 'sj/orch_cd/evalx/work/milestone/raw_g3t_20261114/admission/DENSE_MANIFEST.json'
OLD = LANE / 'work/n13/ret/native/paired/results/items.jsonl'
OLD_LOAD = OLD.parent / 'LOAD_RECEIPT.json'
REQUEST = OLD.parent.parent / 'request.json'


def install(tree=TREE):
    sys.dont_write_bytecode = True
    for p in (LANE, Path(tree)):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def pin(path):
    return dict(path=str(Path(path).resolve()), sha256=sha(path))


def checked(path, expected):
    if sha(path) != expected:
        raise ValueError('sha256 mismatch: ' + str(path))
    return Path(path)


def rows(path):
    with Path(path).open() as f:
        return [json.loads(line) for line in f if line.strip()]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def policy():
    name = '_parity_reader_policy'
    return sys.modules.get(name) or module(C8R / 'reader_policy.py', name)


def key(task):
    return 'devrows:' + task['id']


def tasks(settings):
    result = [t for p in settings.get('tasks', TASKS) for t in rows(p)]
    if len({key(t) for t in result}) != len(result):
        raise ValueError('duplicate task keys')
    request = read(settings.get('request', REQUEST))
    selected = {key(t): t for t in result}
    missing = set(request['keys']) - set(selected)
    if missing or len(request['keys']) != len(set(request['keys'])):
        raise ValueError('request task keys missing or duplicated: ' + str(sorted(missing)))
    return [selected[k] for k in request['keys']]
