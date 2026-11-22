"""Opaque proof for the job roots of the CPU check (kit a/5.py) and the GPU job (kit BATCH.sh), with the
package's own common.opaque() and FORBIDDEN, and the package's own vendor namespace(), environment(),
physical() and process guard building the argv, environment and paths. argv: <kit dir> <payload dir>."""
import io
import json
import os
import random
import re
import string
import subprocess
import sys
import tarfile
import uuid
from pathlib import Path

KIT, PAYLOAD = Path(sys.argv[1]), Path(sys.argv[2])
sys.path[:0] = [str(PAYLOAD), str(PAYLOAD / 'orchard_h10/vendor')]
from orchard_h10.common import opaque, FORBIDDEN, install_process_guard  # noqa: E402
import orchard_job as J  # noqa: E402
import orchard_results as R  # noqa: E402

pkg = KIT / 'pkg'
token = json.loads((pkg / '0.json').read_text())['token']
inputs = json.loads((pkg / 'a/1.json').read_text())
with tarfile.open(pkg / '0.tgz') as t:
    cfg = json.load(t.extractfile('9.json'))
out = []


def ok(values):
    opaque(values)
    return len(values)


# 1. The roots exactly as the placed code writes them.
cpu_src = (pkg / 'a/5.py').read_text()
cpu_line = re.findall(r"^\s*root=Path\('/tmp'\)/\((.+?)\);root\.mkdir\(mode=0o700\)$", cpu_src, re.M)
assert len(cpu_line) == 1 and 'mkdtemp' not in cpu_src, 'CPU root line differs'
batch = (pkg / 'BATCH.sh').read_text()
gpu_line = re.findall(r"^r=Path\('/tmp'\)/\((.+)\)$", batch, re.M)
assert len(gpu_line) == 1 and 'mkdtemp' not in batch, 'GPU root line differs'


class FakeOS:
    def __init__(self, pid): self.pid = pid
    def getpid(self): return self.pid


def cpu_root(job, pid):
    return Path('/tmp') / eval(cpu_line[0], dict(os=FakeOS(pid), job=str(job)))


def gpu_root(job):
    return Path('/tmp') / eval(gpu_line[0], dict(j=str(job)))


# 2. Structural proof: no forbidden word can occur in any root for any digits.
assert all(re.fullmatch('[a-z0-9]+', w) for w in FORBIDDEN)           # never spans '/', '-', '=', '.', '_'
hexonly = [w for w in FORBIDDEN if re.fullmatch('[0-9a-f]+', w)]
assert hexonly == [], hexonly                                           # 'a'+digits+hex token, uuid, return token
digit_a = [w for w in FORBIDDEN if re.fullmatch('a?[0-9]+', w) or re.fullmatch('[0-9]+', w)]
assert digit_a == [], digit_a                                           # 'a<job>' and '<pid>' components
assert not any(w in 'tmp' for w in FORBIDDEN)
out.append('structural: %d words; none fits [0-9a-f]+ or a?[0-9]+; none spans a separator' % len(FORBIDDEN))

# 3. Grid: every launch the bootstrap builds, scanned per (job, pid).
rng = random.Random(20261122)
jobs = [100000, 171253, 174264, 174294, 999999, 1000000, 9999999] + [rng.randrange(10**5, 10**7) for _ in range(300)]
pids = [1, 9, 10, 4194304, 9999999] + [rng.randrange(1, 10**7) for _ in range(5)]
env_base = dict(PATH='/usr/bin:/bin', HOME='/home/jjyeung', USER='jjyeung', CUDA_VISIBLE_DEVICES='')
logical = cfg['logical']


def environment(root, threads, cuda):
    real = Path.mkdir
    Path.mkdir = lambda self, *a, **k: None  # environment() makes cache/temp/home; scan names only
    try:
        env = J.environment(root)
    finally:
        Path.mkdir = real
    env = {k: v for k, v in env.items() if 'sam' not in k.lower()}
    env.update(OMP_NUM_THREADS=threads, MKL_NUM_THREADS=threads, OPENBLAS_NUM_THREADS=threads, CUDA_VISIBLE_DEVICES=cuda)
    return [f'{k}={v}' for k, v in env.items()]


def guarded_pool_argv(root, action, pool, tok, local=None):
    """R.pool_operation's argv as the installed guard rewrites it (real code, Popen recorded)."""
    seen = []

    class Stop(Exception):
        pass

    def recorder(argv, *a, **k):
        seen.append((list(argv), k.get('env'), k.get('cwd')))
        raise Stop
    real_popen, real_wb = subprocess.Popen, Path.write_bytes
    subprocess.Popen = recorder
    Path.write_bytes = lambda self, data: len(data)  # the guard's copy to root/6.py; scan only
    try:
        install_process_guard(root)
        try:
            R.pool_operation(action, str(pool), tok, local=local)
        except Stop:
            pass
    finally:
        subprocess.Popen, Path.write_bytes = real_popen, real_wb
    assert len(seen) == 1
    argv, env, cwd = seen[0]
    assert str(root / '6.py') in argv
    return argv + ([f'{k}={v}' for k, v in env.items()] if env else []) + ([cwd] if cwd else [])


n_cpu = n_gpu = 0
saved_env = dict(os.environ)
for job in jobs:
    os.environ.clear(); os.environ.update(env_base, SLURM_JOB_ID=str(job))
    py = inputs['python']
    for pid in pids:
        r = cpu_root(job, pid)
        assert re.fullmatch(r'/tmp/a[0-9]+-[0-9]+', str(r)) and str(r) == '/tmp/a%d-%d' % (job, pid)
        n_cpu += ok([str(r)])
        n_cpu += ok(guarded_pool_argv(r, 'test', r / 'wpool', token))
        ns = J.namespace(r)
        n_cpu += ok(environment(r, '8', ''))
        for argv in (ns + [py, '-B', '-I', str(r / 'a/5.py'), str(r / 'a/0.json')],
                     ns + [py, '-B', '-I', str(r / 'a/5.py'), str(r / 'a/1.json')],
                     ns + [py, '-B', '-I', str(r / '7.py'), str(r / 'a/1.json')]):
            n_cpu += ok(argv)
    g = gpu_root(job)
    assert str(g) == '/tmp/a%d%s' % (job, token)
    rt = cfg['token'] + format(job, '08x')
    n_gpu += ok([str(g), sys.executable, '-I', '-s', '-B', str(g / '0.py'), str(g)])  # BATCH.sh execv
    n_gpu += ok(guarded_pool_argv(g, 'test', cfg['pool'], rt))
    o = J.physical(g, logical + '/r')
    local = o.parent / ('r_' + rt + '_' + uuid.uuid4().hex)
    n_gpu += ok(guarded_pool_argv(g, 'publish', cfg['pool'], rt, local))
    n_gpu += ok(guarded_pool_argv(g, 'receipt', cfg['pool'], rt, local))
    uri = R.GCS_ROOT + '/' + rt + '/result.tar.gz'
    n_gpu += ok(['gcloud', 'storage', 'cp', str(local / 'result.tar.gz'), uri, uri + '#1795312345678901'])
    ns = J.namespace(g)
    n_gpu += ok(environment(g, '16', '0'))
    for argv in (ns + [py, '-B', '-I', str(g / 'a/5.py'), str(g / 'a/0.json')],
                 ns + [py, '-B', '-I', str(g / '7.py'), str(g / 'a/1.json')],
                 ['nvidia-smi', '--query-gpu=uuid,name,memory.used', '--format=csv']):
        n_gpu += ok(argv)
os.environ.clear(); os.environ.update(saved_env)
out.append('grid: %d job ids (6-7 digits) x %d pids (1-7 digits); CPU strings scanned %d, GPU strings scanned %d; all opaque'
           % (len(jobs), len(pids), n_cpu, n_gpu))
out.append('example CPU root %s; GPU root %s' % (cpu_root(174294, 2192596), gpu_root(174294)))

# 4. The failing path still fails, and the old generated suffix trips at the measured rate.
bad = '/tmp/a174294c8b836b4ae5365wh1sx88/6.py'
try:
    opaque([bad]); raise SystemExit('FAIL old path passed')
except ValueError as e:
    out.append('old path refused: ' + str(e))
chars = 'abcdefghijklmnopqrstuvwxyz0123456789_'  # tempfile._RandomNameSequence alphabet
trip = sum(any(w in 'a174294c8b836b4ae536' + ''.join(rng.choice(chars) for _ in range(8)) for w in FORBIDDEN)
           for _ in range(200000))
out.append('old mkdtemp suffix trips the guard in %.2f%% of draws (200,000 sampled)' % (100 * trip / 200000))
print('\n'.join(out))
print('PASS')
