"""Named, read-only integration roots."""
from pathlib import Path
import importlib.util
import sys
import os
import json
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parents[1]
OFFKIT = BASE / 'kit'
R = BASE / 'builds/R'
C8 = BASE / 'in/c8r/sj/orch_cd/evalx/work/milestone/native/out2'
V1 = BASE / 'in/v1c/code'
REVSI = BASE / 'in/kit_revsi'
VSI = BASE / 'in/x27/kit'
B04 = Path('/scratch/jjyeung/orch_n30/b04_e2ehook')
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449')
RET544 = Path('/scratch/jjyeung/orch_n30/b01_d0guard/work/ret544')
TOKENIZER = B04 / 'work/n13/obj/base/models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a'
if (ROOT/'vendor/ACTIVE.json').is_file():
    for name, relative in json.loads((ROOT/'vendor/ACTIVE.json').read_text()).items():
        globals()[name] = ROOT/relative
# A packed worker resolves only registered paths under its staged root.
if os.environ.get('A0_ROOTS'):
    spec = json.loads(Path(os.environ['A0_ROOTS']).read_text())
    for name in ('OFFKIT','R','C8','V1','REVSI','VSI','B04','TREE','RET544','TOKENIZER'):
        if name not in spec:raise ValueError('missing staged root: '+name)
        value=Path(spec[name])
        if value.is_absolute() or '..' in value.parts:raise ValueError('staged roots must be relative')
        globals()[name]=ROOT/value
for p in (OFFKIT, B04, TREE):
    if str(p) not in sys.path:
        sys.path.append(str(p))
if (ROOT/'out/OFFKIT_EXTERNAL_PINS.json').is_file():
    import hashlib
    package=importlib.util.find_spec('offkit')
    if package is None or package.origin is None:
        raise ValueError('missing owner-supplied offkit package')
    offkit_root=Path(package.origin).parent
    for name, expected in json.loads((ROOT/'out/OFFKIT_EXTERNAL_PINS.json').read_text())['files'].items():
        if hashlib.sha256((offkit_root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('owner-supplied offkit content differs: '+name)

def module(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    try:
        spec.loader.exec_module(obj)
    except BaseException:
        sys.modules.pop(name,None)
        raise
    return obj

def evaluator(benchmark='revsi999t32'):
    p = str(REVSI / 'reader/evaluator' if benchmark=='revsi999t32' else R/'kit/vsi/reader/evaluator')
    if p not in sys.path:
        sys.path.insert(0, p)
    return module('_native_official_scoring_'+benchmark, Path(p) / 'scoring.py')

def r_launcher():
    return module('_native_build_r', R / 'kit/rebind.py')
