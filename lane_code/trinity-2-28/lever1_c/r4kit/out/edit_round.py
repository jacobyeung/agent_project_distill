from pathlib import Path
p=Path('build.py');s=p.read_text().replace("token='b'+digest(frozen)[:12]", "token='c82f06ad913e4'")
s=s.replace("source_blob=gzip.compress(jd(sources),mtime=0)", "source_blob=storage.pack(jd(sources))")
s=s.replace("payload={'1.json':jd(data),'2.json':jd(cfg),'6.json':b'{}\\n',", "payload={'1.json':storage.pack(jd(data)),'2.json':storage.pack(jd(cfg)),'6.json':b'{}\\n',\n             '9.py':wrap((ROOT/'src/storage.py').read_bytes()),\n             '10.py':wrap((ROOT/'src/batch.py').read_bytes()),")
s=s.replace("ROOT = Path(__file__).resolve().parent", "ROOT = Path(__file__).resolve().parent\nimport importlib.util\n_spec=importlib.util.spec_from_file_location('a_storage',ROOT/'src/storage.py')\nstorage=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(storage)")
p.write_text(s)
p=Path('src/control.py');s=p.read_text().replace('import time\n','import time\nimport signal\nfrom contextlib import contextmanager\n')
a=s.index('def opaque(');b=s.index('\ndef sha(',a)
s=s[:a]+'''# Exact external ABI names; the values never receive a blanket exemption.
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
    def expire(*unused): raise Deadline('E01')
    signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, max(.001, min(seconds, end-time.time())))
    try: yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)

''' +s[b:]
s=s.replace("return json.loads(Path(path).read_text())", "value = json.loads(Path(path).read_text())\n    return json.loads(bytes.fromhex(value['a0'])) if isinstance(value, dict) and set(value)=={'a0'} else value")
s=s.replace("Path(path).write_text(json.dumps(obj, sort_keys=True)+'\\n')", "Path(path).write_text(json.dumps({'a0':json.dumps(obj, sort_keys=True).encode().hex()})+'\\n')")
s=s.replace('stdout=subprocess.PIPE, stderr=subprocess.PIPE)', 'stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)')
a=s.index('def materialize(');b=s.index('\ndef fetch(',a)
s=s[:a]+'''def materialize(p, root):
    C = codec(p)
    sources = C.loads((p/'8.bin').read_bytes())
    C.materialize(root, sources)
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
                S.extract_stream(f, root/archive['destination'], None, archive['expanded_bytes'], links=True)
    for f in cfg['inputs']['files'].values():
        with bounded(end):
            q = J.physical(root, f['path'])
            assert q.stat().st_size == f['bytes'] and sha(q) == f['sha256']
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
        write(records/'2.json', dict(passed=False, error=hashlib.sha256((type(error).__name__+str(error)).encode()).hexdigest()))
    if not (records/'1.json').exists():
        n = 0
        if (records/'0.jsonl').exists():
            with (records/'0.jsonl').open('rb') as f: n = sum(1 for _ in f)
        write(records/'1.json', dict(passed=False, mode=mode, records=n, frozen=cfg['frozen'],
            artifact=cfg['export']['artifact']['sha256'], tools_served=0,
            max_new_tokens=64, external_components_loaded=False, status='failed'))
    result_names = [q for q in records.iterdir() if q.is_file() and q.name in ('0.jsonl','1.json','2.json')]
    assert sum(q.stat().st_size for q in result_names) <= LIMIT-100000
    dest = p/'a'/mode; dest.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tarfile.open(dest/'0.tgz', 'w:gz') as t:
        for q in result_names: t.add(q, arcname=q.name, recursive=False)
    receipt = dict(passed=code==0 and error is None and read(records/'1.json')['passed'],
        package=sha(p/'0.json'), payload=sha(p/'0.tgz'), frozen=cfg['frozen'],
        bytes=(dest/'0.tgz').stat().st_size, sha256=sha(dest/'0.tgz'),
        seconds=time.time()-started, code=code, job=job)
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
        J, local = prepare(p, root, cfg, job, min(end, started+600))
        code = launch(root, local, cfg, mode, end, J)
    except BaseException as exc:
        error = exc
    finally:
        signal.signal(signal.SIGTERM, previous)
        with bounded(started+1780, 50):
            receipt = finalize(p, records, cfg, mode, job, started, code, error)
    return 0 if receipt['passed'] else 1

''' +s[b:]
s=s.replace("sources = json.loads(gzip.decompress((p/'8.bin').read_bytes()))", "sources = codec(p).loads((p/'8.bin').read_bytes())")
s=s.replace("assert receipt['package'] == sha(p/'0.json') and receipt['frozen'] == cfg['frozen']", "assert receipt['package'] == sha(p/'0.json') and receipt['frozen'] == cfg['frozen']\n    assert receipt['payload'] == sha(p/'0.tgz')")
a=s.index("    elif action == 'work':");b=s.index("    elif action == 'fetch':",a)
s=s[:a]+'''    elif action == 'work':
        sink = os.open(os.devnull, os.O_WRONLY)
        os.dup2(sink, 1); os.dup2(sink, 2); os.close(sink)
        raise SystemExit(work(p))
'''+s[b:]
p.write_text(s)
