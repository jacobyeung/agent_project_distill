import contextlib
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import tempfile
import time


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def put(p, obj):
    with Path(p).open('x') as f:
        json.dump(obj, f, separators=(',', ':'), allow_nan=False)


def load(p):
    return json.loads(Path(p).read_text())


def verify(p):
    for name, h in load(p/'3.json').items():
        if sha(p/name) != h:
            raise ValueError('E20')
    spec = importlib.util.spec_from_file_location('a2', p/'2.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    c = load(p/'1.json')
    if m.forecast(c) > 1500:
        raise ValueError('E21')
    for row in c['x3']:
        for a in range(3):
            m.binding(row, a)
    return c, m


def alarm(*args):
    raise TimeoutError('E22')


def execute(p, c, m):
    start = time.time()
    job = os.environ.get('SLURM_JOB_ID', '')
    if not job.isdigit():
        raise ValueError('E23')
    end = min(float(os.environ.get('SLURM_JOB_END_TIME', start+1800)), start+1800)
    root = Path(tempfile.mkdtemp(prefix='a'+job+'-', dir='/tmp'))
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(max(1, int(min(600, end-time.time()-90))))
    stage_start = time.time()
    z = c['xf']
    old = Path(c['xg'])
    if sha(old/'0.tgz') != c['xh']:
        raise ValueError('E24')
    code = root/'p'
    code.mkdir()
    with tarfile.open(old/'0.tgz') as t:
        for item in t:
            name = Path(item.name)
            if not item.isfile() or name.is_absolute() or '..' in name.parts:
                raise ValueError('E25')
            dest = code/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as f:
                f.write(t.extractfile(item).read())
    sys.path.insert(0, str(code))
    cm = importlib.import_module(z[0])
    old_cfg = getattr(cm, z[1])(old)
    s, j, _, _, _ = getattr(cm, z[2])()
    getattr(j, z[3])(root, job=job)
    # Use the existing pinned runtime and inputs.
    inputs = load(old/'a/1.json')
    if sha(old/'a/1.json') != c['xi']:
        raise ValueError('E26')
    getattr(importlib.import_module(z[4]), z[5])(root, old_cfg, inputs, s, j)
    signal.alarm(0)
    elapsed = time.time()-start
    remaining = m.forecast(c)-c['x7'][0]
    if elapsed+remaining > 1500 or time.time()+remaining > end-60:
        raise ValueError('E27')
    for name in ('sj', 'fsw', 'm/ap'):
        (root/name).mkdir(parents=True, exist_ok=True)
    env = getattr(j, z[6])(root)
    env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8')
    for name in ('2.py',):
        (root/name).write_bytes((p/name).read_bytes())
    current = dict(c, xe=end-30)
    put(root/'1.json', current)
    argv = getattr(j, z[7])(root)+[c['xj'], '-I', '-s', '-B', str(root/'2.py'),
                                 str(root/'1.json'), str(root/'5.json')]
    getattr(cm, z[8])(argv)
    completed = subprocess.run(argv, env=env, cwd=root, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=max(1, end-time.time()-30))
    if not (root/'5.json').is_file():
        raise ValueError('E28')
    data = load(root/'5.json')
    data.update(staging_seconds=stage_start and elapsed, total_seconds=time.time()-start,
                exit_code=completed.returncode)
    return data


def main():
    mode, p = int(sys.argv[1]), Path(sys.argv[2])
    c, m = verify(p)
    if mode == 0:
        result = m.run(c, stub=True, only=1)
        if not result['complete'] or len(result['rows']) != 1:
            raise ValueError('E29')
        put(p/'4.json', dict(passed=True, input_sha256=sha(p/'1.json'),
                           files=load(p/'3.json'), estimate_seconds=m.forecast(c)))
        return 0
    if mode == 2:
        check = load(p/'4.json')
        if check['files'] != load(p/'3.json') or check['input_sha256'] != sha(p/'1.json') or not check['passed']:
            raise ValueError('E30')
        return 0
    if mode != 1:
        raise ValueError('E31')
    result = dict(schema=1, token=c['x0'], stub=False, complete=False, rows=[], error='E32')
    try:
        with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            result = execute(p, c, m)
    except Exception as e:
        result['error'] = type(e).__name__
    finally:
        signal.alarm(0)
        raw = m.write(p/'5.json', result)
        put(p/'5.1.json', dict(schema=1, token=c['x0'], input_sha256=sha(p/'1.json'),
            sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), complete=result['complete'],
            stub=False, job=os.environ.get('SLURM_JOB_ID', '0')))
    return 0 if result['complete'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('E99', file=sys.stderr)
        raise SystemExit(1)
