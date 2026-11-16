"""Prepare, verify, and label the two accepted direct readers."""
import argparse
import base64
import fcntl
import hashlib
import io
import importlib.util
import json
from pathlib import Path
import re
import shlex
import os
import signal
import subprocess
import time
import sys
import tarfile
import xnames as X

ROOT = Path(__file__).resolve().parents[1]
KIT = Path(__file__).resolve().parent
sys.path.append('/scratch/jjyeung/orch_n30/b07_offread/kit')
OFFKIT_MODULES = ('bind.py', 'report.py', 'spec.py', 'adapt_direct.py', 'frames.py', '__init__.py')


def verify_offkit_pins():
    """Check the resolved package before importing or using any offkit code."""
    pins = json.loads((ROOT/'out/OFFKIT_PINS.json').read_text())
    if set(pins) != set(OFFKIT_MODULES):
        raise ValueError('OFFKIT_PINS.json must cover all six imported modules')
    spec = importlib.util.find_spec('offkit')
    if spec is None or spec.origin is None or spec.submodule_search_locations is None:
        raise ValueError('offkit is not a source package')
    directory = Path(spec.origin).resolve().parent
    if [Path(p).resolve() for p in spec.submodule_search_locations] != [directory]:
        raise ValueError('offkit package search path differs from its source')
    for name in OFFKIT_MODULES:
        path = directory/name
        if hashlib.sha256(path.read_bytes()).hexdigest() != pins[name]:
            raise ValueError('offkit content pin mismatch: '+name)
        module_name = 'offkit' if name == '__init__.py' else 'offkit.'+name[:-3]
        loaded = sys.modules.get(module_name)
        if loaded is not None and Path(loaded.__file__).resolve() != path.resolve():
            raise ValueError('offkit loaded module differs from its pinned source: '+name)


verify_offkit_pins()
from offkit.bind import bind, ledger_append, check_ledger, sha256_file, verify_binding, binding_sha256
from offkit.adapt_direct import from_return
from offkit import report as reports
verify_offkit_pins()
NAMES = {'vsibench5130': 'vsi', 'revsi999t32': 'revsi'}
POOL = '/project/community/jjyeung/okh7/9e6b70a213c84fd0'
LEDGER = '/scratch/jjyeung/orch_n30/b07_offread/out/OFFICIAL_READ_LEDGER.jsonl'


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def launcher(benchmark):
    directory = KIT/NAMES[benchmark]/'launcher'
    sys.path.insert(0, str(directory))
    import orchard_launcher as L
    if L.ROOT != directory:
        raise ValueError('Use a fresh process for each benchmark')
    return L


def unpack(raw):
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        files = {}
        for m in archive:
            if not m.isfile() or m.name in files or Path(m.name).is_absolute() or '..' in Path(m.name).parts:
                raise ValueError('Unsafe packet')
            files[X.logical_path(m.name)] = archive.extractfile(m).read()
        return files


def boot_files(path):
    text=Path(path).read_text()
    raw=re.search(r"^raw=bytes.fromhex\('([^']+)'",text,re.M)
    if raw:return unpack(bytes.fromhex(raw[1]))
    raw = re.search(r"^raw=base64.b64decode\('([^']+)'", text, re.M)
    return unpack(base64.b64decode(raw[1]))


def checked(destination):
    verify_offkit_pins()
    d = Path(destination)
    b = json.loads((d/'BINDING.json').read_text())
    verify_binding(b)
    L = launcher(b['benchmark'])
    c = json.loads((d/'CONFIG.json').read_text())
    L.validate_batch((d/'BATCH.sh').read_text(), c)
    pins = json.loads((d/'BATCH.pin.json').read_text())
    if sha256_file(d/'BATCH.sh') != pins['sha256'] or sha256_file(d/'CONFIG.json') != pins['config_sha256']:
        raise ValueError('Prepared packet was tampered with')
    if (c.get('x0') != b['binding_sha256'] or c.get('x1') != b['export']['sha256']
            or c.get('mode') != b['mode']):
        raise ValueError('Binding differs from the packet')
    return b, c, L


def prepare(a):
    verify_offkit_pins()
    if not re.fullmatch('[a-f][0-9a-f]{8,32}', a.token or ''):
        raise ValueError('Token must be opaque hexadecimal with a leading a-f')
    b = bind(a.benchmark, a.export, 'direct', mode=a.mode,
             init_selection=a.init_selection, ledger=a.ledger)
    step = None
    if b['export']['kind'] == 'done':
        m = re.fullmatch(r'q8/8865619b/359fcc3c_m(200|400|600|800|1000)\.tar', b['export']['object'])
        if not m:
            raise ValueError('The selected completion record has an unregistered lineage or step')
        step = int(m[1])
        # The reviewed parser also rejects extra lines, tabs, and noncanonical spacing.
        L = launcher(a.benchmark)
        import export_stage as E
        rec = E.parse_done(Path(a.export[5:]).read_bytes(), '359fcc3c', step)
        if rec['sha256'] != b['export']['sha256']:
            raise ValueError('Completion record changed')
    L = launcher(a.benchmark)
    d = Path(a.destination)
    c = L.prepare(a.token, d, mode=a.mode, pool=POOL, **({'media_root':'/project/community/jjyeung/okh7/313db5a47f11ff0c/'} if a.benchmark=='revsi999t32' else {}))
    files = boot_files(d/'BATCH.sh')
    c.update(x0=b['binding_sha256'], x1=b['export']['sha256'], x2=int(step is not None))
    if step is not None:
        c['x3'] = b['export']['bytes']
        c['phase_b'] = False
        c['spec']['step'] = step
        artifact = dict(kind='c1_export', path=str(L.J.FSW/'ap/8865619b/runs/359fcc3c'/('m'+str(step))/'artifact.json'), sha256=None)
        c['spec']['artifact'] = artifact
        c['spec']['models']['cp1m200'] = dict(artifact)
        c['plan_sha256'] = L.canonical(c['spec'])
    files['bootstrap/CONFIG.json'] = (json.dumps(c, sort_keys=True)+'\n').encode()
    script = L.render_batch(L.tar_bytes(files), a.token)
    L.validate_batch(script, c)
    (d/'BATCH.sh').write_text(script)
    dump(d/'CONFIG.json', c)
    dump(d/'BATCH.pin.json', dict(sha256=sha256_file(d/'BATCH.sh'), config_sha256=sha256_file(d/'CONFIG.json')))
    dump(d/'BINDING.json', b)
    ledger = ROOT/'work/ORCHARD_LEDGER.jsonl'
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open('a') as f:
        f.write(json.dumps(dict(token=a.token, benchmark=a.benchmark, export=b['export'],
                               binding_sha256=b['binding_sha256'], mode=a.mode, destination=str(d)))+'\n')
    checked(d)
    return dict(binding_sha256=b['binding_sha256'], batch_sha256=sha256_file(d/'BATCH.sh'))


def validate_live(c, L):
    if c.get('proof_only') or c.get('bootstrap_parent','/tmp') != '/tmp':
        raise ValueError('A local fixture cannot be submitted')
    if c['launcher_pins'] != {n:sha256_file(L.ROOT/n) for n in L.CORE}:
        raise ValueError('Launcher sources changed after preparation')
    if canonical(c['spec']) != c['plan_sha256']:
        raise ValueError('Plan differs')


def record(a):
    b, c, L = checked(a.destination)
    validate_live(c, L)
    path = Path(a.ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Serialize validation and append across both benchmark invocations.
    with path.with_suffix(path.suffix+'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        check_ledger(path, b['export'], b['benchmark'])
        if b['mode'] == 'production' and path.exists():
            for line in path.read_text().splitlines():
                r = json.loads(line)
                if all(r.get(k) == v for k,v in dict(export_sha256=b['export']['sha256'], benchmark=b['benchmark'], reader='direct', mode='production').items()):
                    raise ValueError('Production submission is already recorded')
        result = L.submission_record(a.destination)
        if b['mode'] == 'production':
            ledger_append(path, b)
        return result


def governed_transfer(argv, output, errors, size, token):
    """Register a stopped source and a live rate limiter before payload IO."""
    helpers = Path('/scratch/jjyeung/io_governor')
    for name in ('register.py','ratelimit.py'):
        if not (helpers/name).is_file():
            raise ValueError('The IO governor helpers are unavailable')
    lane = 'r'+token
    record = Path('/data3/jjyeung/orch_n13_20261026/io_governor/streams')/(lane+'.json')
    if record.exists():
        raise ValueError('An IO stream record already exists; reconcile it before fetching')
    stop_code = 'import os,signal,sys,subprocess;os.kill(os.getpid(),signal.SIGSTOP);raise SystemExit(subprocess.call(sys.argv[1:]))'
    source = subprocess.Popen([sys.executable,'-B','-c',stop_code,*argv],stdout=subprocess.PIPE,stderr=errors)
    pacer = None
    try:
        pacer = subprocess.Popen([sys.executable,'-B',str(helpers/'ratelimit.py'),'-q','-L','1000','-B','65536'],
                                 stdin=source.stdout,stdout=output,stderr=errors)
        source.stdout.close()
        deadline = time.monotonic()+30
        while True:
            state = Path(f'/proc/{source.pid}/stat').read_text().rsplit(')',1)[1].split()[0]
            ready = Path(f'/proc/{pacer.pid}/comm').read_text().strip()=='ratelimit'
            if state=='T' and ready: break
            if source.poll() is not None or pacer.poll() is not None or time.monotonic()>deadline:
                raise RuntimeError('The stopped IO pipeline did not become ready')
            time.sleep(0.05)
        subprocess.run([sys.executable,'-B',str(helpers/'register.py'),'--lane',lane,'--pid',str(source.pid),
            '--member-pid',str(pacer.pid),'--rl-pid',str(pacer.pid),'--expected-bytes',str(size),
            '--tier','3','--kind','pull','--nominal-mbps','8','--tunnel-mbps','8',
            '--io-weight','1','--tunnel-weight','1','--allow-resume'],check=True,stdout=errors,stderr=errors)
        source_code = source.wait()
        pacer_code = pacer.wait()
        if source_code or pacer_code:
            raise RuntimeError('The governed transfer failed; do not retry it automatically')
        if record.exists():
            record.rename(record.with_name(lane+'.done.'+str(time.time_ns())))
    finally:
        for process in (source,pacer):
            if process is not None and process.poll() is None:
                process.terminate()
                if process is source: os.kill(process.pid,signal.SIGCONT)
                process.wait(timeout=20)


def fetch(a):
    b, c, L = checked(a.destination)
    target = Path(a.destination)/'fetched'
    if a.return_dir:
        source = Path(a.return_dir)
        receipt = json.loads((source/'EXIT.json').read_text())
        import orchard_results as R
        if receipt['token'] != c['token']:
            raise ValueError('Return token differs')
        R.verify(receipt, source/'result.tar.gz', c['plan_sha256'])
        target.mkdir(exist_ok=True)
        for name in ('EXIT.json','result.tar.gz'):
            with (target/name).open('xb') as out, (source/name).open('rb') as inp:
                import shutil
                shutil.copyfileobj(inp, out, 1<<20)
    elif not (target/'result.tar.gz').exists():
        def transfer(argv, out, err, size):
            try:
                governed_transfer(argv, out, err, size, c['token'])
            except Exception as error:
                raise L.TransferRegistrationRequired('Governed transfer stopped; reconcile it without retry: '+str(error)) from error
        L.fetch(a.destination, transfer=transfer)
    import orchard_results as R
    receipt = json.loads((target/'EXIT.json').read_text())
    R.verify(receipt, target/'result.tar.gz', c['plan_sha256'])
    if receipt['token'] != c['token']:
        raise ValueError('Return token differs')
    dest = target/'return'
    if dest.exists():
        raise ValueError('Return is already extracted')
    with tarfile.open(target/'result.tar.gz') as tf:
        x = json.load(tf.extractfile('metadata/X0.json'))
        if x != {k:c[k] for k in ('x0','x1','x2')}:
            raise ValueError('Return binding differs')
        tf.extractall(dest, filter='data')
    return dict(return_dir=str(dest))


def report(a):
    b, c, L = checked(a.destination)
    source = Path(a.return_dir) if a.return_dir else Path(a.destination)/'fetched/return'
    accepted = Path('/scratch/jjyeung/orch_n30/b07_offread/in')/('ret_'+NAMES[b['benchmark']])
    if a.accepted_return:
        if b['export']['kind'] != 'step544' or source.resolve() != accepted:
            raise ValueError('Only the named accepted step544 return is allowed')
    else:
        x = json.loads((source/'metadata/X0.json').read_text())
        if x != {k:c[k] for k in ('x0','x1','x2')}:
            raise ValueError('Return binding differs')
        marker = json.loads((source/'COMPLETE.json').read_text())
        if marker.get('plan_sha256') != c['plan_sha256'] or (source/'FAILED.json').exists():
            raise ValueError('Return completion differs')
    cohort_path = KIT/NAMES[b['benchmark']]/'cohort'/('COHORT_OFFICIAL6.jsonl' if b['benchmark']=='vsibench5130' else 'c5.jsonl')
    cohort = reports.read_jsonl(cohort_path)
    mode = reports.ReadMode(b['benchmark'], 'direct')
    result = {}
    output = Path(a.destination)/'reports'
    native = Path(a.destination)/'native/results/0'
    native.mkdir(parents=True, exist_ok=True)
    alias = native/'budget_16384.jsonl'
    if not alias.exists():
        alias.symlink_to((source/'a0/results/0/items_a0.jsonl').resolve())
    source_rows = {str(r['example_id']):r for r in reports.read_jsonl(source/'a0/results/0/items_a0.jsonl')}
    for arm, budget in (('B2048',2048),('ON16k',16384),('B4096',4096)):
        items = from_return(Path(a.destination)/'native' if budget==16384 else source/'a0', budget)
        for item in items:
            r = source_rows.get(item['id'], {})
            item['source_capped'] = r.get('output_tokens',0)>=16384 or (r.get('max_new_tokens')==16384 and r.get('finish_reason')=='length')
        rep = reports.aggregate(mode, cohort, items)
        # Preserve the accepted scorer's floating-point accumulation order.
        sys.path.insert(0, str(KIT/NAMES[b['benchmark']]/'reader'))
        import official_score
        raw = reports.read_jsonl(source/'a0/results/0'/('items_a0.jsonl' if budget==16384 else f'budget_{budget}.jsonl'))
        legacy = official_score.aggregate(cohort, raw, list(source_rows.values()))
        headline = legacy['six_task_mean' if b['benchmark']=='vsibench5130' else 'five_category_mean']
        corrections = []
        for label, current, expected in [('headline', rep['headline'], headline)] + [
                (g, rep['groups'][g], v) for g,v in legacy['groups'].items()]:
            for field in ('score','percentile_95'):
                old, new = current[field], expected[field]
                aa, bb = (old,new) if isinstance(old,list) else ([old],[new])
                if any(abs(x-y)>1e-12 for x,y in zip(aa,bb)):
                    raise ValueError('Aggregation disagrees with the accepted scorer')
                if old != new: corrections.append(dict(group=label,field=field,offkit=old,accepted_order=new))
                current[field] = new
        rep['float_order_check'] = dict(tolerance=1e-12, corrections=corrections)

        rep = reports.label_report(rep, binding=b, arm='primary',
            role='primary' if budget==2048 else 'secondary', arm_label=arm)
        rep['binding_sha256'] = b['binding_sha256']
        rep['budget'] = arm
        result[arm] = reports.write(rep, output, arm)
    return result


def main():
    verify_offkit_pins()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('prepare','submit-command','record-submission','fetch','report'))
    p.add_argument('--benchmark', choices=tuple(NAMES))
    p.add_argument('--export', default='step544')
    p.add_argument('--init-selection')
    p.add_argument('--ledger', default=LEDGER)
    p.add_argument('--mode', choices=('proof','production'), default='production')
    p.add_argument('--token')
    p.add_argument('--destination', required=True)
    p.add_argument('--return-dir')
    p.add_argument('--accepted-return', action='store_true')
    a = p.parse_args()
    if a.action=='prepare':
        if not a.benchmark: p.error('--benchmark is required for prepare')
        result = prepare(a)
    elif a.action=='submit-command':
        b,c,L = checked(a.destination)
        validate_live(c, L)
        rows = check_ledger(a.ledger, b['export'], b['benchmark'])
        if b['mode']=='production' and any(all(r.get(k)==v for k,v in dict(export_sha256=b['export']['sha256'],benchmark=b['benchmark'],reader='direct',mode='production').items()) for r in rows):
            raise ValueError('Production submission is already recorded')
        print(shlex.join(L.submit_command(c['token'], proof=c['mode']=='proof',job_name=c['job_name'])))
        return
    else:
        result = {'record-submission':record, 'fetch':fetch, 'report':report}[a.action](a)
    print(json.dumps(result, sort_keys=True))


if __name__=='__main__':
    main()
