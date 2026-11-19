"""Small local-only contracts for the A4 Trinity adapter."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LOGICAL = Path('/scratch/jjyeung/b01ec87a6f29b')
STAGE = Path('/scratch/jjyeung/a4228')
VNICE = Path('/data3/shared/scripts/vnice/vnice.sh')
ORDER = ('camera_displacement','camera_rotation','camera_movement_direction','object_abs_distance','room_size_estimation')
SCHEDULE = (3,0,1,2,4)

class Refusal(ValueError):
    pass

def utc():
    return subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w') as f:
        json.dump(value,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())

def append(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps(value,sort_keys=True,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def checked(path, spec):
    path=Path(path)
    if not path.is_file():raise Refusal('Missing file: '+str(path))
    if path.stat().st_size!=spec['bytes']:raise Refusal('Wrong size: '+str(path))
    if sha(path)!=spec['sha256']:raise Refusal('Wrong sha256: '+str(path))
    return path

def local(path):
    path=Path(path).absolute()
    if '..' in path.parts or not path.resolve().is_relative_to('/scratch/jjyeung'):
        raise Refusal('Require a node-local /scratch/jjyeung path: '+str(path))
    return path

def package_root(value):
    value=local(value)
    root=value.parent if (value/'0.tgz').is_file() else value
    if not (root/'package/0.tgz').is_file():raise Refusal('Expected A4 root or its package directory')
    return root

def target_host():
    host=socket.gethostname().split('.')[0]
    if host!='trinity-2-28':raise Refusal('GPU launch is restricted to trinity-2-28; current host is '+host)
    return host

def clean_environment(out, card=''):
    out=local(out)
    env={k:os.environ[k] for k in ('PATH','LD_LIBRARY_PATH') if k in os.environ}
    env.update(CUDA_VISIBLE_DEVICES=card,PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='4',
        MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',NUMEXPR_NUM_THREADS='4')
    for i,key in enumerate(('TMPDIR','XDG_CACHE_HOME','HF_HOME','TRITON_CACHE_DIR','TORCHINDUCTOR_CACHE_DIR','TORCH_HOME')):
        p=out/'cache'/str(i);p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
    return env

def load_module(path, name):
    import importlib.util
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

def install_imports(source):
    source=Path(source)
    sys.path[:0]=[str(source/'b'),str(source/'tree'),str(source)]

def source_check(root, pins):
    root=Path(root)
    for name,spec in pins.items():checked(root/name,spec)
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    if actual!=set(pins):raise Refusal('Unexpected/missing source files: '+str(sorted(actual^set(pins))[:10]))

def deployment(package):
    root=package_root(package);pins=read(HERE/'A4_PINS.json')
    for name,spec in pins['package'].items():checked(root/'package'/name,spec)
    checked(root/'tower_sequence.py',dict(bytes=(HERE/'A4/tower_sequence.py').stat().st_size,sha256=pins['operator_sha256']))
    from tarfile import open as taropen
    with taropen(root/'package/0.tgz') as t:cfg=json.load(t.extractfile('9.json'))
    if canonical(cfg)!=pins['public']['plan_sha256']:raise Refusal('Sealed A4 plan differs')
    cfg.update(pins['public'])
    inputs=read(root/'package/a/1.json');export=read(root/'package/a/export.json')
    if inputs.get('pending') or export.get('pending'):raise Refusal('Use the delivered hydrated A4 package, not the mirror placeholders')
    source_check(root/'src',pins['source'])
    install_imports(root/'src')
    from orchard_h10.export_pins import admit,validate
    validate(export);admit(inputs,cfg,export)
    return root,cfg,inputs,export
