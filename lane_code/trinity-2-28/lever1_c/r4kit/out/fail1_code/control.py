"""Opaque operator entrypoint. No implicit submission or retry."""
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import signal
from contextlib import contextmanager

if not hasattr(Path, 'is_relative_to'):
    def is_relative_to(self, other):
        try:
            self.relative_to(other)
            return True
        except ValueError:
            return False
    Path.is_relative_to = is_relative_to

LIMIT = 50000000
DENY = 'split vsi revsi scannet arkit sam g3t depth distill qwen ground dev bench mask tower reader student teacher k1 t1 word template'.split()


# Exact external ABI names; the values never receive a blanket exemption.
EXTERNAL = {'--dev-bind': 'bubblewrap device-mount ABI', '/dev': 'kernel device namespace'}


def opaque(values):
    for value in map(str, values):
        if value in EXTERNAL: continue
        if value.startswith('CUDA_VISIBLE_DEVICES='):
            value = value[len('CUDA_VISIBLE_DEVICES='):]
        if any(term in value.lower() for term in DENY):
            raise ValueError('Non-opaque public value')


def codec(p):
    spec = importlib.util.spec_from_file_location('a_storage', p/'9.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


class Deadline(Exception): pass


@contextmanager
def bounded(end, seconds=300):
    old = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    entered = time.monotonic()
    def expire(*unused): raise Deadline('E01')
    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, max(.001, min(seconds, end-time.time())))
    try: yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)
        if previous_timer[0]:
            signal.setitimer(signal.ITIMER_REAL, max(.001, previous_timer[0]-(time.monotonic()-entered)), previous_timer[1])


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    value = json.loads(Path(path).read_text())
    return json.loads(bytes.fromhex(value['a0'])) if isinstance(value, dict) and set(value)=={'a0'} else value


def write(path, obj):
    Path(path).write_text(json.dumps({'a0':json.dumps(obj, sort_keys=True).encode().hex()})+'\n')


def check(p):
    pins = read(p/'0.json')
    for name, pin in pins['files'].items():
        assert (p/name).stat().st_size == pin['bytes'] and sha(p/name) == pin['sha256']
    cfg = read(p/'2.json')
    assert p == Path(cfg['package'])
    assert cfg['export']['step'] == 400 and cfg['export']['artifact']['sha256'].startswith('5083243c')
    for group in cfg['assets']['groups']:
        for path, size, h in group:
            assert Path(path).stat().st_size == size
    assert Path(cfg['assets']['bwrap_pin']['path']).stat().st_size == cfg['assets']['bwrap_pin']['bytes']
    for archive in cfg['inputs']['archives']:
        for part in archive['parts']:
            assert Path(part['path']).stat().st_size == part['bytes']
    value = dict(passed=True, package=sha(p/'0.json'), frozen=cfg['frozen'],
                 payload=sha(p/'0.tgz'), artifact=cfg['export']['artifact']['sha256'])
    (p/'a').mkdir(mode=0o700, exist_ok=True)
    write(p/'a/3.json', value)
    return value


def submit(p, mode):
    expected = check(p)
    if mode == 'g':
        receipt = read(p/'a/4.json')
        assert receipt['passed'] and receipt['package'] == expected['package']
        assert receipt['frozen'] == expected['frozen'] and receipt['payload'] == expected['payload']
    cfg = read(p/'2.json')
    flag = p/'a'/('5.txt' if mode == 'c' else '6.txt')
    if flag.exists():
        raise ValueError('Submission already attempted')
    # Mark before invoking sbatch: an interrupted submission cannot be retried.
    flag.write_text('pending\n')
    args = ['sbatch','--parsable','--account=mt01','--partition=general','--nodes=1',
            '--ntasks=1','--cpus-per-task=16','--mem=200G','--time=00:30:00',
            '--exclude=orchard-community-4','--no-requeue','--chdir=/tmp',
            '--job-name='+p.name,'--output='+str(p/'a/8.log'),
            '--error='+str(p/'a/9.log'), '--export=A_M='+mode]
    if mode == 'g':
        args.append('--gres=gpu:1')
    env = dict(PATH='/usr/local/bin:/usr/bin:/bin', HOME=os.environ['HOME'], USER=os.environ['USER'])
    opaque(args); opaque(k+'='+v for k,v in env.items())
    result = subprocess.run(args, input=(p/'4.sh').read_bytes(), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if result.returncode:
        write(p/'a/10.json', dict(passed=False, code=result.returncode,
                                error=hashlib.sha256(result.stderr).hexdigest()))
        raise ValueError('Submission failed; no retry')
    job = result.stdout.decode().strip().split(';')[0]
    assert job.isdigit()
    flag.write_text(job+'\n')
    print(job)


def materialize(p, root):
    C = codec(p)
    sources = C.loads((p/'8.bin').read_bytes())
    C.materialize(root, {k:v for k,v in sources.items() if k.startswith('v/')})
    import orchard_stage as S
    import orchard_job as J
    return S, J


def prepare(p, root, cfg, job, end):
    with bounded(end):
        S, J = materialize(p, root)
    with bounded(end): S.room(root)
    with bounded(end): J.storage_proof(root, job=job)
    stage = root/'a'; stage.mkdir()
    local = root/'p'; local.mkdir()
    with bounded(end):
        assert sha(p/'0.tgz') == read(p/'0.json')['files']['0.tgz']['sha256']
        with (p/'0.tgz').open('rb') as f:
            S.extract_stream(f, local, None, 32*1024**2)
        codec(p).materialize(local, codec(p).loads((local/'8.bin').read_bytes()))
    for i, group in enumerate(cfg['assets']['groups']):
        parts = [dict(path=path, bytes=n, sha256=h) for path,n,h in group]
        target = stage/str(i)
        with bounded(end): S.copy_parts(parts, target, lambda x:Path(x['path']).open('rb'))
        with bounded(end): S.unpack(target, root, links=True)
    with bounded(end):
        S.copy_parts([cfg['assets']['bwrap_pin']], root/'bwrap', lambda x:Path(x['path']).open('rb'))
        (root/'bwrap').chmod(0o700)
    for i, archive in enumerate(cfg['inputs']['archives']):
        target = stage/('a'+str(i))
        with bounded(end):
            S.copy_parts(archive['parts'], target, lambda x:Path(x['path']).open('rb'), expected_sha=archive['sha256'])
        with bounded(end):
            S.room(root, archive['expanded_bytes'])
            with target.open('rb') as f:
                S.extract_stream(f, root/archive['destination'], None, archive['expanded_bytes'], links=True,
                                 retain_roots=None if archive['destination'].endswith('/f') else ('m400','p0','b','o','f','v'))
    for f in cfg['inputs']['files'].values():
        with bounded(end):
            q = J.physical(root, f['path'])
            raw = codec(p).raw(q.read_bytes()) if q.suffix=='.json' else None
            assert (len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']) if raw is not None else (q.stat().st_size==f['bytes'] and sha(q)==f['sha256'])
    return J, local


def launch(root, local, cfg, mode, end, J):
    for name in ('sj','fsw','m/ap'): (root/name).mkdir(parents=True, exist_ok=True)
    env = J.environment(root)
    env.pop('VLLM_USE_FLASHINFER_SAMPLER', None)
    env.update(OMP_NUM_THREADS='16', MKL_NUM_THREADS='16', OPENBLAS_NUM_THREADS='16')
    env['CUDA_VISIBLE_DEVICES'] = '' if mode == 'c' else os.environ['CUDA_VISIBLE_DEVICES']
    if mode == 'g': assert env['CUDA_VISIBLE_DEVICES'] and ',' not in env['CUDA_VISIBLE_DEVICES']
    argv = J.namespace(root)+[cfg['inputs']['python'],'-I','-s','-B',str(local/'5.py'),str(local),mode,str(end-10)]
    opaque(argv); opaque(k+'='+v for k,v in env.items())
    remaining = end-time.time()
    if remaining <= 10: raise Deadline('E02')
    return subprocess.run(argv, env=env, timeout=remaining).returncode


def finalize(p, records, cfg, mode, job, started, code, error=None):
    records.mkdir(parents=True, exist_ok=True)
    if error is not None:
        write(records/'2.json', codec(p).diagnostic(error))
    # A deadline may interrupt a write. Publish only complete arm pairs and
    # reconstruct malformed/missing summaries rather than losing the return.
    C = codec(p)
    content = {}; completed = []; n = 0
    if (records/'0.jsonl').exists():
        with (records/'0.jsonl').open('rb') as f:
            while True:
                first, second = f.readline(262145), f.readline(262145)
                if not first: break
                try:
                    a, b = C.loads(first), C.loads(second)
                    if a['i'] != b['i'] or (a['a'],b['a']) != (0,1): break
                    if sum(map(len, completed))+len(first)+len(second) > LIMIT-1000000: break
                except (ValueError, KeyError, TypeError): break
                completed.extend((first,second)); n += 2
        content['0.jsonl'] = b''.join(completed)
    try:
        summary = read(records/'1.json')
        assert isinstance(summary, dict) and type(summary['passed']) is bool
        if mode == 'g' and summary.get('records') != n: summary['passed'] = False
    except (OSError, ValueError, KeyError, AssertionError):
        summary = dict(passed=False, mode=mode, status='failed')
    summary.update(records=n, frozen=cfg['frozen'], artifact=cfg['export']['artifact']['sha256'],
                   tools_served=0, max_new_tokens=64, external_components_loaded=False)
    if code or error is not None: summary['passed'] = False
    write(records/'1.json', summary)
    content['1.json'] = (records/'1.json').read_bytes()
    for name in ('2.json', '4.json'):
        if (records/name).exists():
            raw = (records/name).read_bytes()
            assert len(raw) <= 150000
            content[name] = raw
    if (records/'3.jsonl').exists():
        lines = []
        with (records/'3.jsonl').open('rb') as stream:
            for line in stream:
                try: C.loads(line)
                except (ValueError, TypeError): break
                if len(line) > 8192 or len(lines) >= 74: break
                lines.append(line)
        content['3.jsonl'] = b''.join(lines)
    dest = p/'a'/mode; dest.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tarfile.open(dest/'0.tgz', 'w:gz') as t:
        for name, raw in content.items():
            item = tarfile.TarInfo(name); item.size = len(raw); item.mode = 0o600
            t.addfile(item, io.BytesIO(raw))
    receipt = dict(passed=code==0 and error is None and read(records/'1.json')['passed'],
        package=sha(p/'0.json'), payload=sha(p/'0.tgz'), frozen=cfg['frozen'],
        bytes=(dest/'0.tgz').stat().st_size, sha256=sha(dest/'0.tgz'),
        seconds=time.time()-started, code=code, job=job, mode=mode)
    assert receipt['bytes'] <= LIMIT
    write(dest/'1.json', receipt)
    if mode == 'c': write(p/'a/4.json', receipt)
    return receipt


def work(p, root=None):
    started = time.time()
    mode = os.environ.get('A_M', 'g'); job = os.environ.get('SLURM_JOB_ID', '0')
    if mode not in ('c','g'): mode = 'g'
    cfg = read(p/'2.json')
    root = Path(root) if root is not None else Path('/tmp')/('a'+cfg['token']+job)
    records = root/'p/a'; code = 1; error = None
    end = min(started+1730, float(os.environ.get('SLURM_JOB_END_TIME', started+1800))-70)
    previous = signal.getsignal(signal.SIGTERM)
    def stop(*unused): raise Deadline('E03')
    signal.signal(signal.SIGTERM, stop)
    try:
        with bounded(end, 60):
            current = check(p)
            assert job.isdigit()
            if mode == 'g':
                accepted = read(p/'a/4.json')
                assert accepted['passed'] and all(accepted[k] == current[k] for k in ('package','payload','frozen'))
            root.mkdir(mode=0o700)
        with bounded(min(end, started+600), 600):
            J, local = prepare(p, root, cfg, job, min(end, started+600))
        with bounded(end+5, 1735):
            code = launch(root, local, cfg, mode, end, J)
    except BaseException as exc:
        error = exc
    finally:
        signal.signal(signal.SIGTERM, previous)
        with bounded(started+1780, 50):
            receipt = finalize(p, records, cfg, mode, job, started, code, error)
    return 0 if receipt['passed'] else 1


def fetch(p, dest, mode='g'):
    if mode not in ('c', 'g'): raise ValueError('E04')
    opaque([str(p),str(dest)])
    cfg = read(p/'2.json')
    source = p/'a'/mode
    receipt = read(source/'1.json')
    assert receipt['mode'] == mode
    assert receipt['package'] == sha(p/'0.json') and receipt['frozen'] == cfg['frozen']
    assert receipt['payload'] == sha(p/'0.tgz')
    assert receipt['bytes'] <= LIMIT and (source/'0.tgz').stat().st_size == receipt['bytes']
    assert sha(source/'0.tgz') == receipt['sha256']
    # Use the base kit's authenticated, bounded framed-stream transport.
    sources = codec(p).loads((p/'8.bin').read_bytes())
    import types
    m = types.ModuleType('a1')
    exec(compile(sources['v/stdout_transfer.py'], 'a1', 'exec'), m.__dict__)
    m.LIMIT = LIMIT
    dest.mkdir(mode=0o700)
    with io.BytesIO() as out:
        m.emit(source/'0.tgz', out, cfg['frozen'], 'complete' if receipt['passed'] else 'failed')
        with (dest/'0.stream').open('xb') as packed:
            packed.write(codec(p).pack(out.getvalue()))
        out.seek(0)
        with (dest/'0.log').open('xb') as log:
            m.receive(out, dest/'0.tgz', cfg['frozen'], log)
    write(dest/'1.json', receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    p = Path(__file__).resolve().parent
    action = sys.argv[1]
    if action == 'check':
        print(json.dumps(check(p), sort_keys=True))
    elif action in ('cpu','submit'):
        submit(p, 'c' if action=='cpu' else 'g')
    elif action == 'work':
        sink = os.open(os.devnull, os.O_WRONLY)
        os.dup2(sink, 1); os.dup2(sink, 2); os.close(sink)
        raise SystemExit(work(p))
    elif action == 'fetch':
        fetch(p, Path(sys.argv[2]).resolve(), sys.argv[3] if len(sys.argv)>3 else 'g')
    else:
        raise SystemExit(2)
