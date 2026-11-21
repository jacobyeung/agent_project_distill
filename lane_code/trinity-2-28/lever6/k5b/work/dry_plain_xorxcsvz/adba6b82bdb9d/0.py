import csv
import hashlib
import importlib
import importlib.util
import io
import gzip
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time

LIMIT = 3000
WRITE_TEST_BYTES = 131072
RESULT_CAP = 6_000_000
DET_CODE = 3
KEEP = 4096
# Mount sources the namespace binds; staging creates only some of them.
BINDS = ('sj', 'fsw', 'm/ap')
# Worker modes: real GPU arms and the real CPU unit. Local tests swap in the stub modes.
MODES = dict(g='g', c='c')


def diagnostics():
    spec = importlib.util.spec_from_file_location('a9', Path(__file__).with_name('9.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def u(value):
    return bytes.fromhex(value).decode()


def error_path(p, mode, group=None):
    return p/('4.err' if mode == 0 else ('6' if mode == 2 else '5')+str(group)+'.err')


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def put(p, obj, cap=RESULT_CAP):
    raw = json.dumps(obj, separators=(',', ':'), allow_nan=False).encode()
    if len(raw) > cap:
        raise ValueError('E33')
    with Path(p).open('xb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    return raw


def load(p):
    return json.loads(Path(p).read_text())


def verify(p):
    pins = load(p/'3.json')
    for name, h in pins.items():
        if sha(p/name) != h:
            raise ValueError('E20')
    c = load(p/'1.json')
    if c['xp']['sha256'] != pins['8.gz'] or len(c['x3']) < 1 or c['x0'] != p.name:
        raise ValueError('E21')
    arms = sorted(a for g in c['xq'] for a in g)
    if arms != list(range(len(c['xr']))) or any(t*c['x7']['factor'] > LIMIT for t in c['xt']):
        raise ValueError('E21')
    return c


def write_test(p, name):
    """Prove the result directory takes a durable write before any long work."""
    path = p/(name+'.wt')
    data = os.urandom(WRITE_TEST_BYTES)
    with path.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    if path.stat().st_size != WRITE_TEST_BYTES or sha(path) != hashlib.sha256(data).hexdigest():
        raise ValueError('E38')
    return dict(bytes=WRITE_TEST_BYTES, sha256=hashlib.sha256(data).hexdigest())


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


def stage(c, root):
    """Stage the pinned runtime, weights and frames exactly as the placed package stages them."""
    z = [u(x) for x in c['xf']]
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
    getattr(j, z[3])(root, job=os.environ['SLURM_JOB_ID'])
    inputs = load(old/'a/1.json')
    if sha(old/'a/1.json') != c['xi']:
        raise ValueError('E26')
    getattr(importlib.import_module(z[4]), z[5])(root, old_cfg, inputs, s, j)
    return cm, j, z


def ready(root):
    """Create every bind source the namespace needs, after staging and before any launch."""
    for name in BINDS:
        (root/name).mkdir(parents=True, exist_ok=True)


def job_root(job):
    """Job-local root whose name holds only digits after its prefix, so no generated letter reaches a launch."""
    for n in range(100):
        root = Path('/tmp')/('a%s-%d%s' % (job, os.getpid(), '-%d' % n if n else ''))
        try:
            root.mkdir(mode=0o700)
            return root
        except FileExistsError:
            continue
    raise ValueError('E27')


def cards():
    """Identify the visible card(s) by UUID and PCI bus id from outside the namespace."""
    visible = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    try:
        q = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid,pci.bus_id', '--format=csv,noheader'],
                           capture_output=True, text=True, timeout=30,
                           env=dict(PATH='/usr/bin:/bin', CUDA_VISIBLE_DEVICES=visible))
        return parse_cards(q.stdout, visible, q.returncode)
    except Exception as e:
        return dict(visible=visible, rows=[], error=diagnostics().detail(e)['type'][:40])


def parse_cards(text, visible, status=0):
    rows = []
    for line in csv.reader(io.StringIO(text)):
        parts = [x.strip() for x in line]
        if len(parts) == 3 and parts[0].isdigit() and parts[1].startswith('GPU-'):
            rows.append(dict(index=int(parts[0]), uuid=parts[1], bus=parts[2]))
    if len(rows) == 1:
        chosen = rows[0]
    else:
        chosen = next((r for r in rows if visible in (r['uuid'], str(r['index']))), None)
    return dict(visible=visible, rows=rows[:8], uuid=chosen and chosen['uuid'], bus=chosen and chosen['bus'],
                status=status)


def prepare(p, c, root, j, z):
    """Extract the fixed plane and authenticate every frame of every capture on job disk."""
    with gzip.open(p/'8.gz', 'rb') as f:
        raw = f.read(c['xp']['bytes']+1)
    if len(raw) != c['xp']['bytes'] or hashlib.sha256(raw).hexdigest() != c['xp']['raw_sha256']:
        raise ValueError('E36')
    with (root/'8.bin').open('xb') as f:
        f.write(raw)
    frames = getattr(j, z[9])(root, c['xc'])
    count = 0
    for row in c['x3']:
        if len(row['h']) != row['n']:
            raise ValueError('E37')
        for h in row['h']:
            q = frames/h[:2]/(h+'.png')
            if sha(q) != h:
                raise ValueError('E37')
            count += 1
    return count


def launch(c, root, cm, j, z, arm, mode, warn, env, end, p=None, code=1, group=None):
    out = root/('a%d%s.json' % (arm, 'w' if warn else ''))
    argv = getattr(j, z[7])(root)+[c['xj'], '-I', '-s', '-B', str(root/'2.py'), str(root/'1.json'),
                                   str(out), str(arm), mode, str(warn)]
    # The same checks the placed package's process guard applies: argv, environment and working directory.
    getattr(cm, z[8])(argv)
    getattr(cm, z[8])(['%s=%s' % kv for kv in env.items()]+[str(root)])
    gpu = cards() if mode == 'g' else None
    log = root/'9.err'
    before = log.stat().st_size if log.exists() else 0
    signal.alarm(max(1, int(end-time.time()-20)))
    started = time.time()
    try:
        completed = diagnostics().capture(argv, keep=KEEP, env=env, cwd=root)
    finally:
        signal.alarm(0)
    wall = time.time()-started
    value = load(out) if out.is_file() else dict(arm=arm, status='missing', complete=False, records=[])
    receipt = load(out.with_suffix('.1.json')) if out.with_suffix('.1.json').is_file() else None
    if receipt is not None and receipt['sha256'] != sha(out):
        raise ValueError('E39')
    value.update(exit_code=completed.returncode, wall_seconds=wall)
    if gpu is not None:
        value['card'] = gpu
    rc = completed.returncode
    if rc:
        kept = getattr(completed, 'kept', None) or dict(c='X0', b=0)
        value['child'] = dict(c=kept['c'], x=rc, s=round(wall, 3), b=kept['b'])
        recorded = (log.stat().st_size if log.exists() else 0) > before
        expected = rc == DET_CODE and value.get('status') == 'nondeterministic_op'
        if not recorded and not expected and p is not None:
            # The arm left no error record: record the opaque stderr class, exit code and wall time.
            diagnostics().record(error_path(p, code, group), dict(type='RuntimeError', code='E94', files=[],
                                                                 status=rc, c=kept['c'], s=round(wall, 3), a=arm))
    return value


def execute(p, c, mode, group=None):
    start = time.time()
    job = os.environ.get('SLURM_JOB_ID', '')
    if not job.isdigit():
        raise ValueError('E23')
    end = min(float(os.environ.get('SLURM_JOB_END_TIME', start+LIMIT)), start+LIMIT)
    root = job_root(job)
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(max(1, int(min(900, end-time.time()-120))))
    cm, j, z = stage(c, root)
    ready(root)
    count = prepare(p, c, root, j, z)
    signal.alarm(0)
    staged = time.time()-start
    for name in ('2.py', '9.py'):
        (root/name).write_bytes((p/name).read_bytes())
    stop = end-150
    current = dict(c, xe=stop, xl=str(root/'8.bin'), xu=str(root/'9.err'))
    put(root/'1.json', current)
    base = getattr(j, z[6])(root)
    # As the placed package's runner does: drop variables whose names carry a deny-listed fragment.
    base = {k: v for k, v in base.items() if u('73616d') not in k.lower()}
    base.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8')
    result = dict(staging_seconds=staged, frames_verified=count, arms=[], job=job)
    try:
        if mode == 0:
            if time.time()+120 > stop:
                raise ValueError('E28')
            env = dict(base, CUBLAS_WORKSPACE_CONFIG=':4096:8', CUDA_VISIBLE_DEVICES='',
                       OMP_NUM_THREADS=str(len(os.sched_getaffinity(0))), MKL_NUM_THREADS=str(len(os.sched_getaffinity(0))))
            result['arms'].append(launch(c, root, cm, j, z, 2, MODES['c'], 1, env, stop+60, p, 0))
        else:
            warn = 0
            for arm in c['xq'][group]:
                det = c['xr'][arm][1]
                if time.time()+120 > stop:
                    result['arms'].append(dict(arm=arm, status='budget', complete=False, records=[]))
                    continue
                env = dict(base, CUBLAS_WORKSPACE_CONFIG=':4096:8') if det else dict(base)
                value = launch(c, root, cm, j, z, arm, MODES['g'], warn if det else 0, env, stop+60, p, 1, group)
                if det and not warn and value['exit_code'] == DET_CODE:
                    # Strict mode refused an op: record it and rerun the arm in a fresh process.
                    first = value
                    warn = 1
                    value = launch(c, root, cm, j, z, arm, MODES['g'], 1, env, stop+60, p, 1, group)
                    value['strict_attempt'] = dict(ops=first.get('ops', []), records=len(first.get('records', [])),
                                                   wall_seconds=first['wall_seconds'], exit_code=first['exit_code'])
                result['arms'].append(value)
    finally:
        if (root/'9.err').exists():
            if (root/'9.err').stat().st_size > 16384:
                raise ValueError('E40')
            for line in io.StringIO((root/'9.err').read_text()):
                diagnostics().record(error_path(p, mode, group), json.loads(line))
    result['total_seconds'] = time.time()-start
    return result


def cpu_passed(c, result):
    if len(result['arms']) != 1:
        return False
    a = result['arms'][0]
    total = sum(r['n'] for r in c['x3'])
    if (a.get('status') != 'ok' or not a.get('complete') or a.get('exit_code') != 0 or len(a['records']) != 1
            or a.get('decoded_frames') != total or result['frames_verified'] != total):
        return False
    r = a['records'][0]
    return r['status'] == 'ok' and len(r['cm']) == 32 and len(r['K']) == 32 and r['s'] > 0


def main():
    os.umask(0o077)
    mode, p = int(sys.argv[1]), Path(sys.argv[2])
    group = int(sys.argv[3]) if mode in (1, 2) else None
    c = verify(p)
    if mode == 0:
        admit(c)
        test = write_test(p, '4')
        result = execute(p, c, 0)
        result['write_test'] = test
        put(p/'4.1.json', result)
        if not cpu_passed(c, result):
            raise ValueError('E29')
        put(p/'4.json', dict(passed=True, input_sha256=sha(p/'1.json'), files=load(p/'3.json'),
                             estimate_seconds=c['xt'], write_test=test, job=result['job']))
        return 0
    if group not in range(len(c['xq'])):
        raise ValueError('E31')
    if mode == 2:
        admit(c)
        check = load(p/'4.json')
        if check['files'] != load(p/'3.json') or check['input_sha256'] != sha(p/'1.json') or not check['passed']:
            raise ValueError('E30')
        if (p/('5%d.json' % group)).exists():
            raise ValueError('E30')
        return 0
    if mode != 1:
        raise ValueError('E31')
    result = dict(schema=1, token=c['x0'], group=group, complete=False, arms=[], error='E32')
    try:
        check = load(p/'4.json')
        if check['files'] != load(p/'3.json') or not check['passed']:
            raise ValueError('E30')
        test = write_test(p, '5%d' % group)
        result = dict(result, **execute(p, c, 1, group), write_test=test, error=None)
        result['complete'] = (len(result['arms']) == len(c['xq'][group])
                              and all(a.get('complete') for a in result['arms']))
    except Exception as e:
        result['error'] = type(e).__name__
        diagnostics().record(error_path(p, mode, group), diagnostics().detail(e))
    finally:
        signal.alarm(0)
        try:
            raw = put(p/('5%d.json' % group), result)
        except ValueError:
            for a in result.get('arms', []):
                a['records'] = []
            result.update(complete=False, error='E33')
            raw = put(p/('5%d.json' % group), result)
        put(p/('5%d.1.json' % group), dict(schema=1, token=c['x0'], group=group, input_sha256=sha(p/'1.json'),
            sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), complete=result['complete'],
            job=os.environ.get('SLURM_JOB_ID', '0')))
    return 0 if result['complete'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        mode = int(sys.argv[1]) if sys.argv[1:2] and sys.argv[1].isdigit() else 1
        group = sys.argv[3] if len(sys.argv) > 3 else None
        diagnostics().record(error_path(Path(sys.argv[2]), mode, group), diagnostics().detail(exc))
        print('E99', file=sys.stderr)
        raise SystemExit(1)
