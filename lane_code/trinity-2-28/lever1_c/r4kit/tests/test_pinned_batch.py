"""Batched-versus-serial decode parity in the authenticated pinned Orchard environment.

Usage: test_pinned_batch.py [delivery.tgz] [evidence.json]
Defaults to out/delivery.tgz and out/PINNED_BATCH_CHECKS.json. The worker runs
the delivery's own 9.py/10.py/7.py/8.bin with the pinned interpreter,
site-packages and a4 overlay inside the production namespace constructor, CPU
only (CUDA hidden), with no package doubles.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
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
delivery = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT/'out/delivery.tgz'
evidence_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT/'out/PINNED_BATCH_CHECKS.json'
root = ROOT/'tmp/pinned'
work = root/('b'+uuid.uuid4().hex); work.mkdir()
p = work/'p'; p.mkdir(); (p/'a').mkdir()
with tarfile.open(delivery) as archive:
    for item in archive:
        (p/item.name).write_bytes(archive.extractfile(item).read())
fixtures = work/'f'; fixtures.mkdir()
for name in ('test_carrier_c1_final.py', 'test_carrier_c1.py'):
    shutil.copyfile(ROOT/'in/D400/src/tree/tests'/name, fixtures/name)
worker = work/'w.py'; shutil.copyfile(ROOT/'tests/pinned_batch_worker.py', worker)
cfg = B.storage.loads((p/'2.json').read_bytes())
S, J = ctl.materialize(p, root)
for name in ('fsw', 'm/ap'): (root/name).mkdir(parents=True, exist_ok=True)
namespace = J.namespace(root); namespace[0] = '/usr/bin/bwrap'
for i in range(len(namespace)-2):
    if namespace[i:i+3] == ['--bind', '/tmp', '/tmp']:
        namespace[i:i+3] = ['--dir', '/tmp', '--bind', str(root), str(root)]
        break
namespace += ['--bind', str(root), str(root)]
env = B.storage.job_environment(work, dict(PATH='/usr/bin:/bin', USER='a', CUDA_VISIBLE_DEVICES='',
    OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2'))
report = work/'r.json'
started = time.monotonic()
command = namespace+[cfg['inputs']['python'], '-I', '-s', '-B', str(worker), str(p), str(fixtures), str(report)]
completed = subprocess.run(command, env=env, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(work/'log').write_bytes(completed.stdout+completed.stderr)
result = json.loads(report.read_text()) if report.exists() else dict(passed=False, error='no report')
evidence = dict(passed=completed.returncode == 0 and result.get('passed') is True, tests=4,
    delivery=B.pin(delivery.read_bytes()), returncode=completed.returncode, seconds=time.monotonic()-started,
    interpreter=cfg['inputs']['python'], namespace='production constructor; system bwrap; extracted pinned archives only',
    cuda_visible_devices='', package_doubles=[], work=str(work.relative_to(ROOT)),
    stderr_tail=(completed.stdout+completed.stderr).decode(errors='replace')[-4000:], result=result)
evidence_path.write_text(json.dumps(evidence, indent=2, default=str)+'\n')
summary = dict(passed=evidence['passed'], delivery=evidence['delivery'], transformers=result.get('transformers'),
               error=result.get('error'), seconds=evidence['seconds'], selfcheck=result.get('selfcheck'),
               selfcheck_with_frozen_merge=result.get('selfcheck_with_frozen_merge'),
               scenarios=[{k: s[k] for k in ('name', 'identical', 'finishes', 'steps', 'linear_state_types')}
                          for s in result.get('scenarios', [])])
print(json.dumps(summary, indent=2))
raise SystemExit(0 if evidence['passed'] else 1)
