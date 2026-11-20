"""Fresh CPU rehearsal with native/Python write auditing and a public file inventory."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
job = Path(sys.argv[1]).resolve()
project = Path(sys.argv[2]).resolve()

writes = set()
def observe(event, args):
    paths = []
    if event == 'open' and isinstance(args[0], (str, bytes)):
        if args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            paths = [args[0]]
    elif event in ('os.rename', 'os.link', 'os.symlink'):
        paths = [args[1]]
    for name in paths:
        path = Path(os.fsdecode(name)).resolve()
        if not path.is_relative_to(job): writes.add(str(path))
sys.addaudithook(observe)
spec = importlib.util.spec_from_file_location('c', ROOT/'src/storage.py')
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
env = C.job_environment(job, dict(PATH='/usr/bin:/bin', USER='a', SLURM_JOB_ID='123', CUDA_VISIBLE_DEVICES=''))
os.environ.clear(); os.environ.update(env)
os.chdir(job)
spec = importlib.util.spec_from_file_location('t', ROOT/'tests/test_fixes.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
os.environ.clear(); os.environ.update(env)

def fresh():
    path = job/uuid.uuid4().hex; path.mkdir(); return path

t.fresh = fresh
original_package = t.package
packages = []
def package():
    value = original_package(); packages.append(value); return value
t.package = package
t.Fixes.setUpClass()
test = t.Fixes('test_05_actual_cpu_rehearsal_and_scan')
test.test_05_actual_cpu_rehearsal_and_scan()
local, cfg, _ = packages[-1]

# Publish only the real budgeted package, return and authenticated fetch.
p = project/'a'; p.mkdir(parents=True)
for name, raw in t.FILES.items(): (p/name).write_bytes(raw)
cfg = C.loads(t.FILES['2.json']); cfg['package'] = str(p)
C.store(p/'2.json', cfg)
pins = json.loads((p/'0.json').read_bytes())
pins['files']['2.json'] = t.B.pin((p/'2.json').read_bytes())
(p/'0.json').write_bytes(t.B.jd(pins))
t.ctl.finalize(p, local/'a', cfg, 'c', '123', time.time(), 0)
t.ctl.fetch(p, project/'f', 'c')
t.scan(project)
(job/'1.json').write_text(json.dumps(dict(passed=True, environment=env,
    observed_public_writes=sorted(writes),
    cpu_rehearsal=t.EVIDENCE['cpu_rehearsal'], public_files=[str(x.relative_to(project))
    for x in sorted(project.rglob('*')) if x.is_file()]), indent=2)+'\n')
