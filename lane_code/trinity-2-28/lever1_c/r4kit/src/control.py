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
import fcntl
import resource
from contextlib import contextmanager

if not hasattr(Path, 'is_relative_to'):
    def is_relative_to(self, other):
        try:
            self.relative_to(other)
            return True
        except ValueError:
            return False
    Path.is_relative_to = is_relative_to

LIMIT = 2000000
PROJECT_BUDGET = dict(limit_bytes=50000000, enforced_max_bytes=44000000,
    placement_bytes=20000000, metadata_and_ledger_bytes=2000000,
    returns_bytes=6000000, fetches_bytes=16000000, project_logs_bytes=0)

class BudgetError(Exception): pass


def account(p, key, amount, once=False):
    # Reserve before writing. Slots survive crashes and cannot be reclaimed or retried.
    directory = Path(p)/'a'; directory.mkdir(parents=True, exist_ok=True)
    with (directory/'12.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        journal = directory/'12.jsonl'
        entries = [read_value for read_value in (codec(p).loads(line) for line in journal.read_bytes().splitlines())] if journal.exists() else []
        if key not in ('m', 'rc', 'rg', 'fc', 'fg'): raise BudgetError('E08')
        cap = 3000000 if key.startswith('r') else 8000000 if key.startswith('f') else 1000000
        used = sum(e['bytes'] for e in entries if e['key'] == key)
        if len(entries) >= 128 or sum(e['bytes'] for e in entries)+amount > 23000000 or amount < 0 or used+amount > cap or (once and any(e['key']==key for e in entries)):
            raise BudgetError('E08')
        raw = codec(p).pack(json.dumps(dict(key=key, bytes=amount)))
        assert len(raw) < 1024
        with journal.open('ab') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def public_write(p, path, raw):
    account(p, 'm', len(raw))
    Path(path).write_bytes(raw)


def public_json(p, path, value):
    public_write(p, path, codec(p).pack(json.dumps(value, sort_keys=True)))

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


def monitor(p):
    spec = importlib.util.spec_from_file_location('a_monitor', p/'11.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def phase(p, root, name, **extra):
    M = monitor(p)
    M.mark(codec(p), root/'p/a', name, **extra)
    if M.memory_over(os.environ.get('A_M', 'g'), strict=os.environ.get('A_G') == '1'):
        raise MemoryError('E06')


def disk_proof(J, root, job):
    proof = J.storage_proof(root, job=job)
    if proof['filesystem'] != 'ext4':
        raise ValueError('E05: ext4 job storage required')
    return proof


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
    public_json(p, p/'a/3.json', value)
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
    public_write(p, flag, b'pending\n')
    args = ['sbatch','--parsable','--account=mt01','--partition=general','--nodes=1',
            '--ntasks=1','--cpus-per-task=16','--mem=200G','--time=00:30:00',
            '--exclude=orchard-community-4','--no-requeue','--chdir=/tmp',
            '--job-name='+p.name,'--output=/tmp/'+p.name+'-%j.8.log',
            '--error=/tmp/'+p.name+'-%j.9.log', '--export=A_M='+mode]
    if mode == 'g':
        args.append('--gres=gpu:1')
    env = dict(PATH='/usr/local/bin:/usr/bin:/bin', HOME=os.environ['HOME'], USER=os.environ['USER'])
    opaque(args); opaque(k+'='+v for k,v in env.items())
    result = subprocess.run(args, input=(p/'4.sh').read_bytes(), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if result.returncode:
        public_json(p, p/'a/10.json', dict(passed=False, code=result.returncode,
                                error=hashlib.sha256(result.stderr).hexdigest()))
        raise ValueError('Submission failed; no retry')
    job = result.stdout.decode().strip().split(';')[0]
    assert job.isdigit()
    public_write(p, flag, (job+'\n').encode())
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
    with bounded(end):
        proof = disk_proof(J, root, job)
        phase(p, root, 'storage', storage=proof)
        write(root/'7.json', proof)
    with bounded(end): S.room(root)
    stage = root/'a'; stage.mkdir()
    local = root/'p'; local.mkdir(exist_ok=True)
    with bounded(end):
        assert sha(p/'0.tgz') == read(p/'0.json')['files']['0.tgz']['sha256']
        with (p/'0.tgz').open('rb') as f:
            S.extract_stream(f, local, None, 32*1024**2)
        codec(p).materialize(local, codec(p).loads((local/'8.bin').read_bytes()))
    for i, group in enumerate(cfg['assets']['groups']):
        phase(p, root, 'runtime_archive', index=i)
        parts = [dict(path=path, bytes=n, sha256=h) for path,n,h in group]
        target = stage/str(i)
        with bounded(end): S.copy_parts(parts, target, lambda x:Path(x['path']).open('rb'))
        with bounded(end): S.unpack(target, root, links=True)
    with bounded(end):
        S.copy_parts([cfg['assets']['bwrap_pin']], root/'bwrap', lambda x:Path(x['path']).open('rb'))
        (root/'bwrap').chmod(0o700)
    for i, archive in enumerate(cfg['inputs']['archives']):
        phase(p, root, 'input_archive', index=i)
        target = stage/('a'+str(i))
        with bounded(end):
            S.copy_parts(archive['parts'], target, lambda x:Path(x['path']).open('rb'), expected_sha=archive['sha256'])
        with bounded(end):
            S.room(root, archive['expanded_bytes'])
            with target.open('rb') as f:
                S.extract_stream(f, root/archive['destination'], None, archive['expanded_bytes'], links=True,
                                 retain_roots=None if archive['destination'].endswith('/f') else ('m400','p0','b','o','f','v'))
    phase(p, root, 'input_pins')
    for f in cfg['inputs']['files'].values():
        with bounded(end):
            q = J.physical(root, f['path'])
            raw = codec(p).raw(q.read_bytes()) if q.suffix=='.json' else None
            assert (len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']) if raw is not None else (q.stat().st_size==f['bytes'] and sha(q)==f['sha256'])
    return J, local


def launch(root, local, cfg, mode, end, J):
    for name in ('sj','fsw','m/ap'): (root/name).mkdir(parents=True, exist_ok=True)
    env = codec(local).job_environment(root, J.environment(root))
    env.pop('VLLM_USE_FLASHINFER_SAMPLER', None)
    env.update(OMP_NUM_THREADS='16', MKL_NUM_THREADS='16', OPENBLAS_NUM_THREADS='16')
    env['CUDA_VISIBLE_DEVICES'] = '' if mode == 'c' else os.environ['CUDA_VISIBLE_DEVICES']
    if mode == 'g': assert env['CUDA_VISIBLE_DEVICES'] and ',' not in env['CUDA_VISIBLE_DEVICES']
    namespace = J.namespace(root)
    # Expose only this job's ext4 directory, not other jobs' temporary files.
    for i in range(len(namespace)-2):
        if namespace[i:i+3] == ['--bind', '/tmp', '/tmp']:
            namespace[i:i+3] = ['--dir', '/tmp', '--bind', str(root), str(root)]
            break
    argv = namespace+[cfg['inputs']['python'],'-I','-s','-B',str(local/'11.py'),str(local),mode,str(end-10)]
    opaque(argv); opaque(k+'='+v for k,v in env.items())
    remaining = end-time.time()
    if remaining <= 10: raise Deadline('E02')
    # The inner supervisor sees the Python status before bubblewrap can translate it.
    env['A_M'] = mode
    if os.environ.get('A_G') == '1': env['A_G'] = '1'
    return monitor(p=local).supervise(argv, env, root, codec(local), end)


def finalize(p, records, cfg, mode, job, started, code, error=None):
    records.mkdir(parents=True, exist_ok=True)
    if error is not None:
        write(records/'2.json', codec(p).diagnostic(error))
    # A deadline may interrupt a write. Publish only complete arm pairs and
    # reconstruct malformed/missing summaries rather than losing the return.
    C = codec(p)
    content = {}; completed = []; n = 0; budget_failure = False
    if (records/'0.jsonl').exists():
        with (records/'0.jsonl').open('rb') as f:
            while True:
                first, second = f.readline(262145), f.readline(262145)
                if not first: break
                try:
                    a, b = C.loads(first), C.loads(second)
                    if a['i'] != b['i'] or (a['a'],b['a']) != (0,1): break
                    if sum(map(len, completed))+len(first)+len(second) > 1000000:
                        budget_failure = True; break
                except (ValueError, KeyError, TypeError): break
                completed.extend((first,second)); n += 2
        content['0.jsonl'] = b''.join(completed)
    try:
        summary = read(records/'1.json')
        assert isinstance(summary, dict) and type(summary['passed']) is bool
        if mode == 'g' and summary.get('records') != n: summary['passed'] = False
    except (OSError, ValueError, KeyError, AssertionError):
        summary = dict(passed=False, mode=mode, status='failed')
    # Prefer the inner worker's exact wait4 status; retain the namespace status too.
    outcome = dict(returncode=code, signal=-code if code < 0 else None,
                   last_stage=dict(stage='not_started'), peak_rss_bytes=None,
                   stdout_tail_hex='', stdout_bytes_retained=0,
                   stderr_tail_hex='', stderr_bytes_retained=0, gpu_max_allocated_bytes=0, gpu_measured=False)
    has_worker = False
    for directory, key in ((records.parent.parent, 'launcher'), (records, 'worker')):
        try:
            observed = C.loads((directory/'6.json').read_bytes())
            if key == 'worker': outcome.update(observed); has_worker = True
            else: outcome.update(observed); outcome['launcher'] = dict(observed)
        except (OSError, ValueError): pass
    try: outcome['last_stage'] = C.loads((records/'5.json').read_bytes())
    except (OSError, ValueError): pass
    try: outcome['storage'] = C.loads((records.parent.parent/'7.json').read_bytes())
    except (OSError, ValueError): pass
    try: outcome['controller'] = C.loads((records.parent.parent/'q/6.json').read_bytes())
    except (OSError, ValueError): outcome['controller'] = dict(stdout_tail_hex='', stderr_tail_hex='')
    try:
        metrics = C.loads((records/'7.json').read_bytes())
        outcome['peak_rss_bytes'] = max(outcome.get('peak_rss_bytes') or 0, metrics['peak_rss_bytes'])
        outcome.update({k:v for k,v in metrics.items() if k != 'peak_rss_bytes'})
    except (OSError, ValueError): pass
    outcome['peak_rss_bytes'] = max(outcome.get('peak_rss_bytes') or 0, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    outcome['charged_memory_stop_bytes'] = monitor(p).memory_limit(mode)
    # Expose controller output as the primary tails if no child launched.
    if 'launcher' not in outcome and not has_worker:
        outcome.update(outcome['controller'])
    if budget_failure:
        code = 1; summary.update(passed=False, status='project_budget')
    summary['execution'] = outcome
    if code or error is not None:
        try: diagnostic = C.loads((records/'4.json').read_bytes())
        except (OSError, ValueError): diagnostic = dict(passed=False)
        diagnostic['execution'] = outcome
        write(records/'4.json', diagnostic)
    summary.update(records=n, frozen=cfg['frozen'], artifact=cfg['export']['artifact']['sha256'],
                   tools_served=0, max_new_tokens=64, external_components_loaded=False)
    if code or error is not None: summary['passed'] = False
    write(records/'1.json', summary)
    content['1.json'] = (records/'1.json').read_bytes()
    for name in ('2.json', '4.json'):
        if (records/name).exists():
            raw = (records/name).read_bytes()
            assert len(raw) <= 500000
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
    packed = io.BytesIO()
    with tarfile.open(fileobj=packed, mode='w:gz') as t:
        for name, raw in content.items():
            item = tarfile.TarInfo(name); item.size = len(raw); item.mode = 0o600
            t.addfile(item, io.BytesIO(raw))
    archive = packed.getvalue()
    if len(archive) > LIMIT or sum(map(len, content.values())) > LIMIT:
        code = 1
        summary.update(passed=False, status='project_budget', records=0)
        packed = io.BytesIO()
        with tarfile.open(fileobj=packed, mode='w:gz') as t:
            raw = C.pack(json.dumps(summary)); item = tarfile.TarInfo('1.json'); item.size = len(raw)
            t.addfile(item, io.BytesIO(raw))
        archive = packed.getvalue()
    assert len(archive) <= LIMIT
    dest = p/'a'/mode
    account(p, 'r'+mode, 3000000, once=True)
    dest.mkdir(mode=0o700, parents=True, exist_ok=True)
    (dest/'0.tgz').write_bytes(archive)

    receipt = dict(passed=code==0 and error is None and summary['passed'],
        package=sha(p/'0.json'), payload=sha(p/'0.tgz'), frozen=cfg['frozen'],
        bytes=(dest/'0.tgz').stat().st_size, sha256=sha(dest/'0.tgz'),
        seconds=time.time()-started, code=code, job=job, mode=mode, execution=outcome)
    assert receipt['bytes'] <= LIMIT
    raw_receipt = C.pack(json.dumps(receipt, sort_keys=True))
    assert len(raw_receipt) <= 500000
    (dest/'1.json').write_bytes(raw_receipt)
    if mode == 'c': (p/'a/4.json').write_bytes(raw_receipt)
    return receipt


def work(p, root=None):
    import tempfile
    cfg = read(p/'2.json')
    root = Path(root) if root is not None else Path('/tmp')/('a'+cfg['token']+os.environ.get('SLURM_JOB_ID', '0'))
    previous = dict(os.environ); previous_tmp = tempfile.tempdir
    env = codec(p).job_environment(root)
    opaque(k+'='+v for k,v in env.items())
    os.environ.clear(); os.environ.update(env); tempfile.tempdir = env['TMPDIR']
    try:
        return _work(p, root)
    finally:
        os.environ.clear(); os.environ.update(previous); tempfile.tempdir = previous_tmp


def _work(p, root=None):
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
    captured = monitor(p).capture(root/'q', codec(p))
    streams = captured.__enter__()
    try:
        with bounded(end, 60):
            current = check(p)
            assert job.isdigit()
            if mode == 'g':
                accepted = read(p/'a/4.json')
                assert accepted['passed'] and all(accepted[k] == current[k] for k in ('package','payload','frozen'))
            root.mkdir(mode=0o700, exist_ok=True)
            phase(p, root, 'prepare')
        with bounded(min(end, started+600), 600):
            J, local = prepare(p, root, cfg, job, min(end, started+600))
        with bounded(end+5, 1735):
            code = launch(root, local, cfg, mode, end, J)
    except BaseException as exc:
        error = exc
    finally:
        captured.__exit__(None, None, None)
        if streams.over: error = BudgetError('E09')
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
    account(p, 'f'+mode, 8000000, once=True)
    dest.mkdir(mode=0o700)
    with io.BytesIO() as out:
        m.emit(source/'0.tgz', out, cfg['frozen'], 'complete' if receipt['passed'] else 'failed')
        transport = codec(p).pack(out.getvalue())
        receipt_raw = codec(p).pack(json.dumps(receipt, sort_keys=True))
        if len(transport)+receipt['bytes']+len(receipt_raw)+10000 > 8000000:
            raise BudgetError('E10')
        with (dest/'0.stream').open('xb') as packed:
            packed.write(transport)
        out.seek(0)
        with (dest/'0.log').open('xb') as log:
            m.receive(out, dest/'0.tgz', cfg['frozen'], log)
    write(dest/'1.json', receipt)
    print(codec(p).pack(json.dumps(receipt, sort_keys=True)).decode(), end='')


def main():
    p = Path(__file__).resolve().parent
    action = sys.argv[1]
    if action == 'check':
        print(json.dumps(check(p), sort_keys=True))
    elif action in ('cpu','submit'):
        submit(p, 'c' if action=='cpu' else 'g')
    elif action == 'work':
        os.environ['A_G'] = '1'
        raise SystemExit(work(p))
    elif action == 'fetch':
        fetch(p, Path(sys.argv[2]).resolve(), sys.argv[3] if len(sys.argv)>3 else 'g')
    else:
        raise SystemExit(2)


if __name__ == '__main__':
    try: main()
    except BudgetError:
        print(json.dumps({'a0': b'E08'.hex()}))
        raise SystemExit(1)
