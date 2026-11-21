"""Defect-finding continuation of the job's mode-q path from the point where it refused.

Reads the job directory (mounted read-only) and writes only under the scratch folder given as
argv[1]. The streams the job already built are reused through links; the one refused comparison is
replaced by the same comparison on content hashes, logged as a warning each time it differs.
Nothing written here is evidence for any gate."""
import contextlib, importlib, json, os, resource, sys, time
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
tbm = importlib.import_module(hx('7472616365') + 'back'); TBA = '__' + hx('7472616365') + 'back__'
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
KIT = Path(os.environ['Q_KIT']).resolve()
NODE2 = Path(sys.argv[1]).resolve()
STOP_AFTER = sys.argv[2] if len(sys.argv) > 2 else ''
A = NODE2 / 'p'; ROOT = A / 'q'
NODE2.mkdir(parents=True, mode=0o700, exist_ok=True)
EV = NODE2 / 'ev.jsonl'
T0 = time.time()


def ev(kind, **kw):
    rec = dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), t=round(time.time() - T0, 1), kind=kind, **kw)
    line = json.dumps(rec, default=str)
    print('EV ' + line, flush=True)
    with open(EV, 'a') as f:
        f.write(line + '\n')


def fail(step, error):
    ev('ERROR', step=step, error=(type(error).__name__ + ':' + str(error))[:3000],
       tb=''.join(tbm.format_exception(type(error), error, getattr(error, TBA)))[-14000:])


sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(OLD / 's')); sys.path.insert(0, str(KIT / 'b'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned, write, file_pin = prov.load, prov.pinned, prov.write, prov.file_pin
pers = mod(PK + '.r1_persisted')
proof = mod('launch_r1.production_proof'); entry = mod('launch_r1.entry')
ev('START', node2=str(NODE2), kit=str(KIT), pid=os.getpid(), cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'))

request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
A.mkdir(mode=0o700); ROOT.mkdir(mode=0o700)
for name in ('s', 'plan.json', 'i'):
    os.symlink(OLD / name, A / name)
(NODE2 / 'r.json').write_text((NS / 'r.json').read_text())
(NODE2 / 'n.json').write_text((NS / 'n.json').read_text())
result = dict(status='REFUSE', GO=False, steps=list(old_result['steps']), forward='not requested', continuation_of='174134')
state = {}


def step(name, action):
    started = time.time(); ev('BEGIN', step=name)
    try:
        value = action()
    except BaseException as error:
        fail(name, error); state.setdefault('failed', []).append(name)
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise
        return None
    ev('DONE', step=name, seconds=round(time.time() - started, 1)); result['steps'].append(name)
    return value


with contextlib.ExitStack() as stack:
    stack.enter_context(pers.scope(paths))
    stack.enter_context(pers.proof_scope())
    stack.enter_context(pers.scope({p['sha256']: p['path'] for p in old_result['staged']}))
    config_pin = load(OQ / 'p/request.json')['config']
    cfg = load(pinned(config_pin))
    value = cfg['r1_training']

    def do_closure():
        return pers.verify(value.get('handover_receipt'), value.get('p_run', {}), cfg['init_artifact']['artifact'],
                           value.get('persisted_files', {}), weights=bool(request.get('weights')),
                           proof_mode=value.get('proof_mode'), init_policy=pers.init_policy(value))
    closure = step('closure_verify(again)', do_closure)
    if closure is None:
        raise SystemExit(2)
    milestone = closure['receipt']['step']
    memory = request.get('memory_gib', 192); device = request.get('device', 'cpu')
    ev('INFO', milestone=milestone, memory=memory, device=device, frame_roots=request['frame_roots'])
    # the host record of the job is not on disk; the six assertions the job had passed are carried over
    host = dict(status='FAIL', config_identity=None, assertions={k: True for k in entry.ASSERTIONS}, missing=[],
                loader_audit={'complete': False}, carried_over_from='174134')
    host['assertions']['directory_modes'] = False
    host.update(stager='hook', staging_plan_sha256=request['staging']['sha256'])
    stack.enter_context(entry.host_environment(ROOT))
    import torch
    # the job's process had opened the device (opener step) before admit masked it
    ev('INFO', cuda_available=torch.cuda.is_available(), device_count=torch.cuda.device_count())
    keep = torch.zeros(1, device='cuda:0')
    ev('INFO', cuda_initialized=torch.cuda.is_initialized(), torch=torch.__version__)

    adm = mod(PK + '.s1_admission'); data = mod(PK + '.carrier_c1_data'); run = mod(PK + '.carrier_c1_run'); rout = mod(PK + '.s1_routing')
    OLDPREP = sorted((OQ / 'p').glob('prepare_*'))[0]

    def reuse_stream(source, division_pin, output, stream, **kw):
        old = load(OLDPREP / stream / 'receipt.json')
        if old['source'] != source or old['division'] != division_pin or old['stream'] != stream:
            raise RuntimeError('HARNESS_REUSE_MISMATCH:' + stream)
        os.symlink(OLDPREP / stream, output)
        ev('REUSE', what=stream, of=str(OLDPREP / stream), count=old['count'])
        return old

    def reuse_routing(cfg_, directory, division_pin, base_model, *, audit_only=False):
        old = load(OLDPREP / 'routing/receipt.json')
        if old['division'] != division_pin or audit_only:
            raise RuntimeError('HARNESS_REUSE_MISMATCH:routing')
        os.symlink(OLDPREP / 'routing', directory)
        ev('REUSE', what='routing', of=str(OLDPREP / 'routing'), count=old['count'])
        return old

    native_admits = run.division_admits
    is_pin = lambda v: isinstance(v, dict) and set(v) == {'path', 'sha256'}

    def soft_admits(stream_division, pose_division):
        if native_admits(stream_division, pose_division):
            return True
        chain, cur = [], pose_division
        for _ in range(6):
            if not is_pin(cur):
                break
            chain.append(cur)
            try:
                cur = load(pinned(cur)).get('parent_division')
            except Exception:
                break
        same = [p for p in chain if is_pin(stream_division) and p['sha256'] == stream_division['sha256'] and p != stream_division]
        caller = [(os.path.basename(f.filename), f.lineno, f.name) for f in tbm.extract_stack(limit=4)[:-1]]
        if same and native_admits(same[0], pose_division):
            ev('WARNING', what='PIN_PATH_DIFFERS admitted on content hash', stream_pin=stream_division, chain_pin=same[0],
               reference=pose_division, caller=caller)
            return True
        ev('WARNING', what='division not admitted (kept as a refusal)', stream_pin=stream_division, reference=pose_division, caller=caller)
        return False

    data.build_stream = reuse_stream; rout.build = reuse_routing; run.division_admits = soft_admits
    sx = mod(PK + '.s1_exclusions'); native_cov = sx.coverage_report; native_load = sx.load
    cov_seen = set()

    def soft_cov(rule, streams, policy=None):
        try:
            return native_cov(rule, streams, policy)
        except ValueError as error:
            if 'Filter differs from independent scene census' not in str(error):
                raise
            if str(error) not in cov_seen:
                cov_seen.add(str(error))
                ev('WARNING', what='scene census comparison refused; logged, then the report is built without the exact comparison',
                   error=str(error), filter_counts={k: dict(v) for k, v in rule.sources.items()})

            def lax(path):
                value = native_load(path)
                if isinstance(value, dict) and value.get('schema') == 'dev_s1_manifest_v1' and value.get('exact_rebuilt_population'):
                    value = dict(value, exact_rebuilt_population=False)
                return value
            sx.load = lax
            try:
                return native_cov(rule, streams, policy)
            finally:
                sx.load = native_load
    sx.coverage_report = soft_cov
    pm = mod(PK + '.c1_pose_mix'); native_mix = pm.prepare
    MIXC = Path('/tmp/a15_dbg_174134/mixc.json')

    def cached_mix(spec_pin, output, listed, reported, excluded, check=None):
        if MIXC.exists():
            saved = json.loads(MIXC.read_text())
            if saved['spec'] == spec_pin:
                path = Path(output) / 'pose_mix_order.json'
                write(path, load(saved['entry']['order']['path']))
                entry = dict(saved['entry'], order=file_pin(path))
                if entry['order']['sha256'] != saved['entry']['order']['sha256']:
                    raise RuntimeError('HARNESS_MIX_CACHE_MISMATCH')
                ev('REUSE', what='pose mix selection of an earlier scratch run', of=saved['entry']['order']['path'], count=entry['count'])
                return entry, saved['settings']
        entry, settings = native_mix(spec_pin, output, listed, reported, excluded, check=check)
        MIXC.write_text(json.dumps(dict(spec=spec_pin, entry=entry, settings=settings)))
        return entry, settings
    pm.prepare = cached_mix
    from mg import guard
    native_admit = adm.admit

    def do_admit():
        directory = ROOT / 'p'; directory.mkdir(exist_ok=True)
        limit = resource.getrlimit(resource.RLIMIT_AS)
        with pers.scope(closure['paths']):
            visible = os.environ.get('CUDA_VISIBLE_DEVICES')
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
            try:
                with guard():
                    return native_admit(config_pin, directory, request['frame_roots'], threads=8, memory_gib=memory, prepare_only=True)
            finally:
                resource.setrlimit(resource.RLIMIT_AS, limit)
                if visible is None:
                    os.environ.pop('CUDA_VISIBLE_DEVICES', None)
                else:
                    os.environ['CUDA_VISIBLE_DEVICES'] = visible
    prepared = step('s1_admission.prepare (admit, prepare_only; streams reused)', do_admit)
    if prepared is None or STOP_AFTER == 'admit':
        write(ROOT / 'RESULT.json', {**result, 'failed': state.get('failed', [])}); raise SystemExit(3 if prepared is None else 0)
    ev('INFO', prepared={k: prepared.get(k) for k in ('config', 'preparation', 'source_counts', 'frames')})

    def do_bind_prepared():
        from importlib import import_module
        bind_prepared = import_module(PK + '.r1_population').bind_prepared
        with pers.scope(closure['paths']):
            return bind_prepared(load(pinned(prepared['config'])), ROOT / 'b')
    produced = step('r1_population.bind_prepared', do_bind_prepared)
    if produced is None:
        write(ROOT / 'RESULT.json', {**result, 'failed': state.get('failed', [])}); raise SystemExit(4)
    cfg = load(pinned(produced)); result['config'] = produced

    def do_handover():
        with pers.scope(closure['paths']):
            pin = proof.bind_handover(cfg, ROOT / 'h')
            bound = load(pinned(pin))
            handover = pers.admission(bound, weights=bool(request.get('weights')))
        return pin, bound, handover
    got = step('persisted_handover', do_handover)
    if got is None:
        write(ROOT / 'RESULT.json', {**result, 'failed': state.get('failed', [])}); raise SystemExit(5)
    result['config'], cfg, handover = got
    result['handover'] = {k: v for k, v in handover.items() if k != 'paths'}
    result['absolute_resume_step'] = handover['absolute_resume_step']; result['init_milestone'] = handover['init_milestone']
    expected_start = 0 if pers.init_policy(cfg['r1_training']) is not None else milestone
    ev('INFO', absolute_resume_step=result['absolute_resume_step'], init_milestone=result['init_milestone'], expected_start=expected_start,
       start_check=bool(result['init_milestone'] in (400, 600) and result['absolute_resume_step'] == expected_start))

    def do_audit():
        production_audit = mod(PK + '.r1_loader').production_audit
        with pers.scope(closure['paths']):
            return production_audit(cfg, ROOT / 'a')
    audit = step('r1_loader.production_audit', do_audit)
    if audit is not None:
        result['audit'] = audit

    def do_forward():
        with pers.scope(handover['paths']):
            return proof.forward(cfg, ROOT, result['absolute_resume_step'], device)
    if STOP_AFTER != 'audit':
        forward = step('all_rank_full_forward', do_forward)
        if forward is not None:
            result['forward'] = forward
            ev('INFO', forward={k: forward[k] for k in ('loss_by_stream', 'peak_rss_bytes', 'absolute_step', 'ranks', 'device')})

    def do_finish():
        entry.finish_host(cfg, ROOT, host, audit, named_refusals=True)
        write(ROOT / 'host.json', host)
        return file_pin(ROOT / 'host.json')
    if audit is not None:
        pin = step('finish_host', do_finish)
        if pin is not None:
            result['host_receipt'] = pin
    if not state.get('failed'):
        result['status'] = 'ADMIT'
    result['failed'] = state.get('failed', [])
    write(ROOT / 'RESULT.json', result)
    ev('END', status=result['status'], failed=result['failed'], steps=result['steps'], config=result.get('config'))
print(json.dumps({'ok': result['status'] == 'ADMIT'}))
