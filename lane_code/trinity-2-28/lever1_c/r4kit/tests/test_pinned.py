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
def boot(mode):
    package = p if mode == 'c' else root/('p'+uuid.uuid4().hex)
    if mode != 'c':
        package.mkdir()
        with tarfile.open(ROOT/'out/delivery.tgz') as archive:
            for item in archive:
                (package/item.name).write_bytes(archive.extractfile(item).read())
        (package/'a').mkdir()
    run_env = dict(env, A_B='1', A_M=mode)
    started = time.monotonic()
    command = namespace+[cfg['inputs']['python'],'-I','-s','-B',str(package/'5.py'),str(package),mode,str(time.time()+600)]
    result = subprocess.run(command,env=run_env,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (package/'boot.log').write_bytes(result.stdout+result.stderr)
    return result, B.storage.loads((package/'a/10.json').read_bytes()), time.monotonic()-started, package
result, receipt, seconds, _ = boot('c')
# GPU-mode boot in the same pinned environment with CUDA hidden: the required
# GPU entry (triton) must import; optional kernels are recorded, not required.
gpu_result, gpu_receipt, gpu_seconds, gpu_package = boot('g')
gpu_passed = (gpu_result.returncode==0 and gpu_receipt['passed']
    and gpu_receipt['required_modules']==cfg['import_closure']['required_modules']+list(cfg['import_closure']['gpu_only'])
    and set(gpu_receipt['optional_modules'])==set(cfg['import_closure']['gpu_optional'])
    and all(v['fallback_expected'] and not v['present'] and v['origin'] is None for v in gpu_receipt['optional_modules'].values()))
evidence = dict(passed=result.returncode==0 and receipt['passed'] and gpu_passed,tests=2,
    delivery=B.pin((ROOT/'out/delivery.tgz').read_bytes()),receipt=receipt,
    seconds=seconds,returncode=result.returncode,
    gpu_mode=dict(passed=gpu_passed,returncode=gpu_result.returncode,seconds=gpu_seconds,
        bulk_bytes=0,optional_modules=gpu_receipt.get('optional_modules'),
        gpu_only=list(cfg['import_closure']['gpu_only']),modules=gpu_receipt.get('modules'),
        closure_entry=gpu_receipt.get('closure_entry'),exception_message=gpu_receipt.get('exception_message'),
        package=str(gpu_package.relative_to(ROOT)),cuda_visible_devices=''),
    environment=cfg['import_closure']['pinned_environment'],archives=archives,
    package=str(p.relative_to(ROOT)),namespace='production constructor; system bwrap; extracted pinned archives only',
    cuda_visible_devices='',bulk_bytes=0,package_doubles=[],interpreter=cfg['inputs']['python'])
(ROOT/'out/PINNED_CHECKS.json').write_text(json.dumps(evidence,indent=2)+'\n')
assert evidence['passed'], (receipt.get('exception_message'), gpu_receipt.get('exception_message'), gpu_receipt.get('optional_modules'))
assert receipt['required_modules']==cfg['import_closure']['required_modules']
assert receipt['closure_sha256']==cfg['import_closure']['closure_sha256']==gpu_receipt['closure_sha256']
print(json.dumps({k:v for k,v in evidence.items() if k not in ('receipt','archives')},indent=2))
