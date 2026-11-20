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


def opaque(values):
    for value in map(str, values):
        # These are operating-system/CUDA interface names, not experiment names.
        if value in ('--dev-bind','/dev'):
            continue
        if value.startswith('CUDA_VISIBLE_DEVICES='):
            value = value[len('CUDA_VISIBLE_DEVICES='):]
        if any(term in value.lower() for term in DENY):
            raise ValueError('Non-opaque public value')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, obj):
    Path(path).write_text(json.dumps(obj, sort_keys=True)+'\n')


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
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        write(p/'a/10.json', dict(passed=False, code=result.returncode,
                                error=hashlib.sha256(result.stderr).hexdigest()))
        raise ValueError('Submission failed; no retry')
    job = result.stdout.decode().strip().split(';')[0]
    assert job.isdigit()
    flag.write_text(job+'\n')
    print(job)


def materialize(p, root):
    sources = json.loads(gzip.decompress((p/'8.bin').read_bytes()))
    for name, text in sources.items():
        rel = Path(name)
        assert not rel.is_absolute() and '..' not in rel.parts
        target = root/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    sys.path.insert(0, str(root/'v'))
    import orchard_stage as S
    import orchard_job as J
    return S, J


def work(p):
    # Redirect all native-library diagnostics before loading private runtime code.
    sink = os.open(os.devnull, os.O_WRONLY)
    os.dup2(sink, 1); os.dup2(sink, 2); os.close(sink)
    current = check(p)
    cfg = read(p/'2.json')
    mode = os.environ['A_M']
    if mode == 'g':
        accepted = read(p/'a/4.json')
        assert accepted['passed'] and all(accepted[k] == current[k] for k in ('package','payload','frozen'))
    job = os.environ['SLURM_JOB_ID']
    assert job.isdigit() and mode in ('c','g')
    root = Path('/tmp')/('a'+cfg['token']+job)
    root.mkdir(mode=0o700)
    started = time.time()
    end = min(started+1750, float(os.environ.get('SLURM_JOB_END_TIME', started+1800))-30)
    S, J = materialize(p, root)
    S.room(root)
    J.storage_proof(root, job=job)
    stage = root/'a'; stage.mkdir()
    local = root/'p'; local.mkdir()
    assert sha(p/'0.tgz') == read(p/'0.json')['files']['0.tgz']['sha256']
    with (p/'0.tgz').open('rb') as f:
        S.extract_stream(f, local, None, 32*1024**2)
    # The opaque code data is unpacked only in the private allocation directory.
    for name, text in json.loads(gzip.decompress((local/'8.bin').read_bytes())).items():
        if name.startswith('c/'):
            q = local/name; q.parent.mkdir(parents=True, exist_ok=True); q.write_text(text)
    for i, group in enumerate(cfg['assets']['groups']):
        parts = [dict(path=path, bytes=n, sha256=h) for path,n,h in group]
        target = stage/str(i)
        S.copy_parts(parts, target, lambda x:Path(x['path']).open('rb'))
        S.unpack(target, root, links=True)
    bp = cfg['assets']['bwrap_pin']
    S.copy_parts([bp], root/'bwrap', lambda x:Path(x['path']).open('rb'))
    (root/'bwrap').chmod(0o700)
    for i, archive in enumerate(cfg['inputs']['archives']):
        target = stage/('a'+str(i))
        S.copy_parts(archive['parts'], target, lambda x:Path(x['path']).open('rb'), expected_sha=archive['sha256'])
        S.room(root, archive['expanded_bytes'])
        with target.open('rb') as f:
            S.extract_stream(f, root/archive['destination'], None, archive['expanded_bytes'], links=True)
    for f in cfg['inputs']['files'].values():
        q = J.physical(root, f['path'])
        assert q.stat().st_size == f['bytes'] and sha(q) == f['sha256']
    for name in ('sj','fsw','m/ap'):
        (root/name).mkdir(parents=True, exist_ok=True)
    env = J.environment(root)
    env.pop('VLLM_USE_FLASHINFER_SAMPLER', None)
    env.update(OMP_NUM_THREADS='16', MKL_NUM_THREADS='16', OPENBLAS_NUM_THREADS='16')
    env['CUDA_VISIBLE_DEVICES'] = '' if mode == 'c' else os.environ['CUDA_VISIBLE_DEVICES']
    if mode == 'g':
        assert env['CUDA_VISIBLE_DEVICES'] and ',' not in env['CUDA_VISIBLE_DEVICES']
    assert time.time() < end-60
    argv = J.namespace(root)+[cfg['inputs']['python'],'-I','-s','-B',str(local/'5.py'),str(local),mode,str(end-20)]
    opaque(argv); opaque(k+'='+v for k,v in env.items())
    result = subprocess.run(argv, env=env)
    records = local/'a'
    if not records.exists():
        records.mkdir()
    result_names = [q for q in records.iterdir() if q.is_file() and q.name in ('0.jsonl','1.json','2.json')]
    total = sum(q.stat().st_size for q in result_names)
    assert total <= LIMIT-100000
    dest = p/'a'/('c' if mode == 'c' else 'g')
    dest.mkdir(mode=0o700)
    with tarfile.open(dest/'0.tgz', 'w:gz') as t:
        for q in result_names:
            t.add(q, arcname=q.name, recursive=False)
    assert (dest/'0.tgz').stat().st_size <= LIMIT
    receipt = dict(passed=result.returncode==0 and (records/'1.json').exists() and read(records/'1.json')['passed'],
        package=sha(p/'0.json'), payload=sha(p/'0.tgz'), frozen=cfg['frozen'],
        bytes=(dest/'0.tgz').stat().st_size, sha256=sha(dest/'0.tgz'),
        seconds=time.time()-started, code=result.returncode, job=job)
    write(dest/'1.json', receipt)
    if mode == 'c':
        write(p/'a/4.json', receipt)
    raise SystemExit(0 if receipt['passed'] else 1)


def fetch(p, dest):
    opaque([str(p),str(dest)])
    cfg = read(p/'2.json')
    source = p/'a/g'
    receipt = read(source/'1.json')
    assert receipt['package'] == sha(p/'0.json') and receipt['frozen'] == cfg['frozen']
    assert receipt['bytes'] <= LIMIT and (source/'0.tgz').stat().st_size == receipt['bytes']
    assert sha(source/'0.tgz') == receipt['sha256']
    # Use the base kit's authenticated, bounded framed-stream transport.
    sources = json.loads(gzip.decompress((p/'8.bin').read_bytes()))
    import types
    m = types.ModuleType('a1')
    exec(compile(sources['v/stdout_transfer.py'], 'a1', 'exec'), m.__dict__)
    m.LIMIT = LIMIT
    dest.mkdir(mode=0o700)
    with (dest/'0.stream').open('xb') as out:
        m.emit(source/'0.tgz', out, cfg['frozen'], 'complete' if receipt['passed'] else 'failed')
    with (dest/'0.stream').open('rb') as f, (dest/'0.log').open('xb') as log:
        m.receive(f, dest/'0.tgz', cfg['frozen'], log)
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
        try:
            work(p)
        except Exception as e:
            write(p/'a/11.json', dict(passed=False, error=hashlib.sha256((type(e).__name__+str(e)).encode()).hexdigest()))
            raise SystemExit(1)
    elif action == 'fetch':
        fetch(p, Path(sys.argv[2]).resolve())
    else:
        raise SystemExit(2)
