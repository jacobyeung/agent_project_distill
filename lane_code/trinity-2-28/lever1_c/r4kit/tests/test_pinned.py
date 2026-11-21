"""Replay the exact delivered CPU boot in the authenticated Orchard environment."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value
B = module('builder', ROOT/'build.py')
ctl = module('control', ROOT/'src/control.py')
root = ROOT/'tmp/pinned'
archives = json.loads((ROOT/'out/PINNED_ARCHIVES.json').read_text())
p = root/('p'+uuid.uuid4().hex); p.mkdir()
with tarfile.open(ROOT/'out/delivery.tgz') as archive:
    for item in archive:
        (p/item.name).write_bytes(archive.extractfile(item).read())
cfg = B.storage.loads((p/'2.json').read_bytes())
for record in archives[:2]:
    expected = cfg['assets']['groups'][record['group']]
    assert [(n,h) for _,n,h in record['parts']] == [(n,h) for _,n,h in expected]
assert archives[2]['sha256'] == cfg['inputs']['archives'][2]['sha256']
S, J = ctl.materialize(p,root)
for name in ('fsw','m/ap'): (root/name).mkdir(parents=True,exist_ok=True)
(p/'a').mkdir()
namespace = J.namespace(root); namespace[0]='/usr/bin/bwrap'
for i in range(len(namespace)-2):
    if namespace[i:i+3] == ['--bind','/tmp','/tmp']:
        namespace[i:i+3] = ['--dir','/tmp','--bind',str(root),str(root)]
        break
# The fixture root lives under /scratch; expose it after the production /scratch bind.
namespace += ['--bind',str(root),str(root)]
env = B.storage.job_environment(root, dict(PATH='/usr/bin:/bin',USER='a',
    CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16'))
env.update(A_B='1',A_M='c')
started = time.monotonic()
command = namespace+[cfg['inputs']['python'],'-I','-s','-B',str(p/'5.py'),str(p),'c',str(time.time()+600)]
result = subprocess.run(command,env=env,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(p/'boot.log').write_bytes(result.stdout+result.stderr)
receipt = B.storage.loads((p/'a/10.json').read_bytes())
evidence = dict(passed=result.returncode==0 and receipt['passed'],tests=1,
    delivery=B.pin((ROOT/'out/delivery.tgz').read_bytes()),receipt=receipt,
    seconds=time.monotonic()-started,returncode=result.returncode,
    environment=cfg['import_closure']['pinned_environment'],archives=archives,
    package=str(p.relative_to(ROOT)),namespace='production constructor; system bwrap; extracted pinned archives only',
    cuda_visible_devices='',bulk_bytes=0,package_doubles=[],interpreter=cfg['inputs']['python'])
(ROOT/'out/PINNED_CHECKS.json').write_text(json.dumps(evidence,indent=2)+'\n')
assert evidence['passed'], receipt
assert receipt['required_modules']==cfg['import_closure']['required_modules']
assert receipt['closure_sha256']==cfg['import_closure']['closure_sha256']
print(json.dumps({k:v for k,v in evidence.items() if k not in ('receipt','archives')},indent=2))
