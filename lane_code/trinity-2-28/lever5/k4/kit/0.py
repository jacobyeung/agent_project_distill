import hashlib
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import sys
import tarfile
import tempfile
import time


def diagnostics():
    import importlib.util
    spec = importlib.util.spec_from_file_location('a9', Path(__file__).with_name('9.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def error_path(p, mode):
    return p / ('4.err' if mode == 0 else '6.err' if mode == 2 else '5.err')


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
    if m.forecast(c) > c['xv'][1] or c['xq'] != len(m.tasks(c)) or not c['xt']:
        raise ValueError('E21')
    for row in c['x3']:
        for a in range(len(row['x4'])):
            m.binding(row, a)
    return c, m


def alarm(*args):
    raise TimeoutError('E22')


def admit(c):
    p = Path(c['xg'])
    if sha(p/'0.tgz') != c['xh'] or sha(p/'a/1.json') != c['xi']:
        raise ValueError('E34')
    for a in load(p/'a/1.json')['archives']:
        for item in a['parts']:
            if Path(item['path']).stat().st_size != item['bytes']:
                raise ValueError('E35')


def execute(p, c, m, cpu=False):
    start = time.time()
    job = os.environ.get('SLURM_JOB_ID', '')
    if not job.isdigit():
        raise ValueError('E23')
    cap = c['xv'][2] if cpu else c['xv'][0]
    end = min(float(os.environ.get('SLURM_JOB_END_TIME', start+cap)), start+cap)
    root = Path(tempfile.mkdtemp(prefix='a'+job+'-', dir='/tmp'))
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(max(1, int(min(c['x7'][0], end-time.time()-90))))
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
    remaining = c['xv'][3] if cpu else m.forecast(c)-c['x7'][0]
    if elapsed+remaining > cap-120 or time.time()+remaining > end-60:
        raise ValueError('E27')
    dest = root/'8'
    dest.mkdir()
    for archive in ('8.tgz', '10.tgz'):
        with tarfile.open(p/archive) as t:
            for item in t:
                if not item.isfile() or '/' in item.name or not item.name.endswith('.png'):
                    raise ValueError('E36')
                with (dest/item.name).open('xb') as f:
                    f.write(t.extractfile(item).read())
    for name in ('sj', 'fsw', 'm/ap'):
        (root/name).mkdir(parents=True, exist_ok=True)
    env = getattr(j, z[6])(root)
    env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8')
    for name in ('2.py', '9.py'):
        (root/name).write_bytes((p/name).read_bytes())
    current = dict(c, xe=end-30, xl=str(root/'8'), xu=str(root/'9.err'))
    put(root/'1.json', current)
    argv = getattr(j, z[7])(root)+[c['xj'], '-I', '-s', '-B', str(root/'2.py'),
                                 str(root/'1.json'), str(root/'5.json')]
    if cpu:
        argv.append('1')
    getattr(cm, z[8])(argv)
    signal.alarm(max(1, int(end-time.time()-30)))
    try:
        completed = diagnostics().capture(argv, env=env, cwd=root)
    finally:
        signal.alarm(0)
        if (root/'9.err').exists():
            if (root/'9.err').stat().st_size > 16384:
                raise ValueError('E37')
            for line in io.StringIO((root/'9.err').read_text()):
                diagnostics().record(error_path(p, 0 if cpu else 1), json.loads(line))
    if not (root/'5.json').is_file():
        raise ValueError('E28')
    data = load(root/'5.json')
    data['complete'] = data['complete'] and completed.returncode == 0
    data.update(staging_seconds=elapsed, total_seconds=time.time()-start,
                exit_code=completed.returncode)
    return data


def cpu_passed(c, m, result):
    rows, arm = result['rows'], result['rows'][0]['arms'][0] if result['rows'] else {}
    if (not result['complete'] or len(rows) != 1 or result['ran'] != [[0, 0]] or arm.get('status') != 'ok'
            or len(arm['c2w']) != 32 or arm['ids'] != c['x3'][0]['x4'][0]['x0']):
        return False
    decoded = result.get('decoded', [])
    if len(decoded) != len(c['x3']):
        return False
    for row, got in zip(c['x3'], decoded):
        if got['key'] != row['x0'] or len(got['arms']) != len(row['x4']):
            return False
        for a, value in zip(row['x4'], got['arms']):
            if a is not None and (value is None or value['frames'] != len(a['x0'])):
                return False
    return True


def main():
    mode, p = int(sys.argv[1]), Path(sys.argv[2])
    c, m = verify(p)
    if mode == 0:
        admit(c)
        result = execute(p, c, m, cpu=True)
        put(p/'4.1.json', result)
        if not cpu_passed(c, m, result):
            raise ValueError('E29')
        put(p/'4.json', dict(passed=True, input_sha256=sha(p/'1.json'),
                           files=load(p/'3.json'), estimate_seconds=m.forecast(c)))
        return 0
    if mode == 2:
        admit(c)
        check = load(p/'4.json')
        if check['files'] != load(p/'3.json') or check['input_sha256'] != sha(p/'1.json') or not check['passed']:
            raise ValueError('E30')
        return 0
    if mode != 1:
        raise ValueError('E31')
    result = dict(schema=3, token=c['x0'], stub=False, mode='gpu', complete=False, rows=[], error='E32')
    try:
        result = execute(p, c, m)
    except Exception as e:
        result['error'] = type(e).__name__
        diagnostics().record(error_path(p, mode), diagnostics().detail(e))
    finally:
        signal.alarm(0)
        if len(json.dumps(result, separators=(',', ':')).encode()) > 3_000_000:
            result = dict(schema=3, token=c['x0'], stub=False, mode='gpu', complete=False, rows=[], error='E33')
        raw = m.write(p/'5.json', result)
        put(p/'5.1.json', dict(schema=3, token=c['x0'], input_sha256=sha(p/'1.json'),
            sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), complete=result['complete'],
            stub=False, mode='gpu', job=os.environ.get('SLURM_JOB_ID', '0')))
    return 0 if result.get('finished') else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        diagnostics().record(error_path(Path(sys.argv[2]), int(sys.argv[1])), diagnostics().detail(exc))
        print('E99', file=sys.stderr)
        raise SystemExit(1)
