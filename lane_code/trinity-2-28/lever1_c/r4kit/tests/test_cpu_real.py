"""CPU real-batch path, time guard and memory limits, locally and in the pinned environment.

Runs tests/cpu_real_worker.py twice: with the local p1cpu interpreter, and with
the authenticated pinned Orchard interpreter inside the production namespace
constructor (CUDA hidden, no package doubles). Writes out/CPU_REAL_CHECKS.json.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value
B = module('builder', ROOT/'build.py')
ctl = module('control', ROOT/'src/control.py')
work = ROOT/'out'/('r'+uuid.uuid4().hex[:12]); work.mkdir()
runs = {}

def run(name, command, env):
    report = work/(name+'.json')
    started = time.monotonic()
    done = subprocess.run(command+[str(report)], env=env, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (work/(name+'.log')).write_bytes(done.stdout)
    value = json.loads(report.read_text()) if report.exists() else dict(passed=False, error='no report')
    runs[name] = dict(passed=done.returncode == 0 and value.get('passed') is True, returncode=done.returncode,
                      seconds=time.monotonic()-started, result=value,
                      log_tail=done.stdout.decode(errors='replace')[-3000:])

local_env = B.storage.job_environment(work/'l', dict(PATH='/usr/bin:/bin', USER='a', CUDA_VISIBLE_DEVICES='',
    OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2'))
run('local', [sys.executable, '-I', '-s', '-B', str(ROOT/'tests/cpu_real_worker.py')], local_env)

root = ROOT/'tmp/pinned'
package = work/'p'; package.mkdir()
import tarfile
with tarfile.open(ROOT/'out/delivery.tgz') as archive:
    for item in archive:
        (package/item.name).write_bytes(archive.extractfile(item).read())
cfg = B.storage.loads((package/'2.json').read_bytes())
S, J = ctl.materialize(package, root)
for name in ('fsw', 'm/ap'): (root/name).mkdir(parents=True, exist_ok=True)
namespace = J.namespace(root); namespace[0] = '/usr/bin/bwrap'
for i in range(len(namespace)-2):
    if namespace[i:i+3] == ['--bind', '/tmp', '/tmp']:
        namespace[i:i+3] = ['--dir', '/tmp', '--bind', str(root), str(root)]
        break
# Test harness only: expose the kit so the worker can build its tiny fixtures.
namespace += ['--bind', str(root), str(root), '--bind', str(ROOT), str(ROOT)]
pinned_env = B.storage.job_environment(work/'q', dict(PATH='/usr/bin:/bin', USER='a', CUDA_VISIBLE_DEVICES='',
    OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2'))
run('pinned', namespace+[cfg['inputs']['python'], '-I', '-s', '-B', str(ROOT/'tests/cpu_real_worker.py')], pinned_env)

evidence = dict(passed=all(r['passed'] for r in runs.values()) and runs['pinned']['result'].get('transformers') == '5.19.0',
                tests=2, delivery=B.pin((ROOT/'out/delivery.tgz').read_bytes()), work=str(work.relative_to(ROOT)),
                runs=runs, scope='Tiny native hybrid export through the delivered runtime.run(c) CPU real-batch path; '
                'the full step-400 checkpoint runs only in the Orchard CPU preflight.')
(ROOT/'out/CPU_REAL_CHECKS.json').write_text(json.dumps(evidence, indent=2, default=str)+'\n')
print(json.dumps({n: dict(passed=r['passed'], transformers=r['result'].get('transformers'), error=r['result'].get('error'),
                          scenarios=r['result'].get('scenarios'), memory=r['result'].get('memory'))
                  for n, r in runs.items()}, indent=2, default=str))
raise SystemExit(0 if evidence['passed'] else 1)
