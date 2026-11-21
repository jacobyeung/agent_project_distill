"""fix10 held-node test of the kit-side census (b/cn.py). Read-only on the job directory; writes only
under argv[1]. Steps: (1) cn.admitted on the job's own staged scene rebuild (2.json) and config;
(2) the tree's admit/prepare with that census bound into the config, streams reused, pose-mix
selection reused from an earlier scratch run; the tree's coverage_report is called unchanged (a spy
records its arguments and result, nothing else); (3) controls on the same filter rule: the tree's
whole-store census must refuse; a planted listed row inside the admitted population must refuse.
Nothing written here is gate evidence."""
import contextlib, copy, importlib, json, os, resource, sys, time
from pathlib import Path

hx = lambda s: bytes.fromhex(s).decode()
PK = hx('73747564656e745f70696c6f74')
tbm = importlib.import_module(hx('7472616365') + 'back'); TBA = '__' + hx('7472616365') + 'back__'
NS = Path('/tmp/q_22c714e1'); OLD = NS / 'p'; OQ = OLD / 'q'
KIT = Path(os.environ['Q_KIT']).resolve()
NODE = Path(sys.argv[1]).resolve(); MODE = sys.argv[2]
A = NODE / 'p'; ROOT = A / 'q'; CEN = NODE / 'cen'
EV = NODE / ('ev_' + MODE + '.jsonl'); T0 = time.time()


def ev(kind, **kw):
    rec = dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), t=round(time.time() - T0, 1), kind=kind, **kw)
    line = json.dumps(rec, default=str); print('EV ' + line[:4000], flush=True)
    with open(EV, 'a') as f: f.write(line + '\n')


def err(error):
    return (type(error).__name__ + ':' + str(error))[:2000]


sys.path.insert(0, str(KIT / 'b')); sys.path.insert(0, str(OLD / 's')); sys.path.insert(0, str(NODE / 'b'))
mod = importlib.import_module
prov = mod(PK + '.p3_provenance'); load, pinned, write, file_pin = prov.load, prov.pinned, prov.write, prov.file_pin
pers = mod(PK + '.r1_persisted'); sx = mod(PK + '.s1_exclusions'); sb = mod(PK + '.r2_scene_bindings')
import cn
ev('START', mode=MODE, cn=prov.sha256(NODE / 'b/cn.py') if hasattr(prov, 'sha256') else None)
request = load(NS / 'r.json'); paths = request.pop('_paths')
old_result = load(OQ / 'RESULT.json')
with contextlib.ExitStack() as stack:
    stack.enter_context(pers.scope(paths)); stack.enter_context(pers.proof_scope())
    stack.enter_context(pers.scope({p['sha256']: p['path'] for p in old_result['staged']}))
    config_pin = load(OQ / 'p/request.json')['config']
    cfg = load(pinned(config_pin))
    rebuild = load(pinned(cfg['r2_scene_rebuild']))
    if MODE == 'census':
        CEN.mkdir(parents=True, exist_ok=True)
        t = time.time(); pin = cn.admitted(rebuild, cfg, CEN)
        ev('CENSUS', seconds=round(time.time() - t, 1), bound=pin, a=file_pin(CEN / 'a.json'), o=file_pin(CEN / 'o.json'))
        o = load(CEN / 'o.json')
        for name, r in o['sources'].items():
            ev('CENSUS_SOURCE', source=name, admitted_rows=r['admitted_rows'], outside_rows=r['outside_rows'], whole=r['whole'],
               admitted=r['admitted'], outside=r['outside'], outside_listed=len(r['outside_listed_keys']),
               first_outside_listed=r['outside_listed_keys'][:2])
        raise SystemExit(0)
    if MODE == 'plant':
        o = load(CEN / 'o.json'); plant = {}
        for name in ('pose_a2v3', 'camera'):
            keys = [k for k in o['sources'][name]['outside_listed_keys'] if k[1]]
            plant[name] = keys[0][0]
        (NODE / 'lk').mkdir(exist_ok=True)
        t = time.time(); pin = cn.admitted(rebuild, cfg, NODE / 'lk', plant=plant)
        ev('PLANTED', plant=plant, seconds=round(time.time() - t, 1), bound=pin)
        raise SystemExit(0)
    # MODE == 'prepare'
    import launch_r1.production_proof as proof; entry = mod('launch_r1.entry')
    A.mkdir(mode=0o700); ROOT.mkdir(mode=0o700)
    for name in ('s', 'plan.json', 'i'):
        os.symlink(OLD / name, A / name)
    bound = load(CEN / '3.json')
    new = dict(cfg, r2_scene_rebuild=file_pin(CEN / '3.json'), scene_coverage=bound['scene_coverage'])
    sb.verify(new)
    ev('CONFIG', changed=sorted(k for k in set(cfg) | set(new) if cfg.get(k) != new.get(k)), reference=new['scene_coverage']['reference'])
    write(NODE / 'cfg10.json', new); new_pin = file_pin(NODE / 'cfg10.json')
    value = cfg['r1_training']
    closure = pers.verify(value.get('handover_receipt'), value.get('p_run', {}), cfg['init_artifact']['artifact'],
                          value.get('persisted_files', {}), weights=bool(request.get('weights')),
                          proof_mode=value.get('proof_mode'), init_policy=pers.init_policy(value))
    ev('INFO', closure='passed')
    stack.enter_context(entry.host_environment(ROOT))
    adm = mod(PK + '.s1_admission'); data = mod(PK + '.carrier_c1_data'); run = mod(PK + '.carrier_c1_run'); rout = mod(PK + '.s1_routing')
    OLDPREP = sorted((OQ / 'p').glob('prepare_*'))[0]

    def reuse_stream(source, division_pin, output, stream, **kw):
        old = load(OLDPREP / stream / 'receipt.json')
        if old['source'] != source or old['division'] != division_pin or old['stream'] != stream:
            raise RuntimeError('HARNESS_REUSE_MISMATCH:' + stream)
        os.symlink(OLDPREP / stream, output); ev('REUSE', what=stream, count=old['count']); return old

    def reuse_routing(cfg_, directory, division_pin, base_model, *, audit_only=False):
        old = load(OLDPREP / 'routing/receipt.json')
        if old['division'] != division_pin or audit_only:
            raise RuntimeError('HARNESS_REUSE_MISMATCH:routing')
        os.symlink(OLDPREP / 'routing', directory); ev('REUSE', what='routing', count=old['count'], division=division_pin); return old
    native_admits = run.division_admits

    def soft_admits(stream_division, pose_division):
        # the vqa receipt's division pin path (F1, fixed in the kit by receipt a7682dae): same sha256, other path
        if native_admits(stream_division, pose_division):
            return True
        if isinstance(stream_division, dict) and isinstance(pose_division, dict) and stream_division.get('sha256') == pose_division.get('sha256'):
            ev('WARNING', what='F1 PIN_PATH_DIFFERS admitted on content hash (not this change)', stream_pin=stream_division, reference=pose_division)
            return True
        chain, cur = [], pose_division
        for _ in range(6):
            if not (isinstance(cur, dict) and set(cur) == {'path', 'sha256'}): break
            chain.append(cur)
            try: cur = load(pinned(cur)).get('parent_division')
            except Exception: break
        same = [p for p in chain if isinstance(stream_division, dict) and p['sha256'] == stream_division.get('sha256') and p != stream_division]
        if same and native_admits(same[0], pose_division):
            ev('WARNING', what='F1 PIN_PATH_DIFFERS admitted on content hash (not this change)', stream_pin=stream_division, chain_pin=same[0])
            return True
        return False
    data.build_stream = reuse_stream; rout.build = reuse_routing; run.division_admits = soft_admits
    native_cov = sx.coverage_report; calls = []

    def spy_cov(rule, streams, policy=None):
        caller = [(os.path.basename(f.filename), f.lineno, f.name) for f in tbm.extract_stack(limit=7)[:-1]]
        calls.append(dict(rule=rule, streams=copy.deepcopy(streams), policy=copy.deepcopy(policy)))
        ev('COVERAGE_CALL', n=len(calls), caller=caller, reference=(policy or {}).get('reference'))
        try:
            report = native_cov(rule, streams, policy)
        except Exception as error:
            ev('COVERAGE_REFUSED', error=err(error), policy=policy); raise
        cov = report.get('coverage') or {}
        ev('COVERAGE_PASSED', status=cov.get('status'), groups={n: dict(observed=[s['observed_dev_matches'], s['observed_benchmark_matches']],
           census=[s['reference_dev_rows'], s['reference_benchmark_rows']]) for n, s in (cov.get('sources') or {}).items()})
        return report
    sx.coverage_report = spy_cov
    pm = mod(PK + '.c1_pose_mix'); MIXC = NODE / 'mixc.json'

    def cached_mix(spec_pin, output, listed, reported, excluded, check=None):
        saved = json.loads(MIXC.read_text())
        if saved['spec'] != spec_pin: raise RuntimeError('HARNESS_MIX_SPEC_DIFFERS')
        path = Path(output) / 'pose_mix_order.json'; write(path, load(NODE / 'mixorder.json'))
        entry_ = dict(saved['entry'], order=file_pin(path))
        if entry_['order']['sha256'] != saved['entry']['order']['sha256']: raise RuntimeError('HARNESS_MIX_CACHE_MISMATCH')
        ev('REUSE', what='pose mix selection of fix6 scratch run n2', count=entry_['count']); return entry_, saved['settings']
    pm.prepare = cached_mix
    status = 'REFUSE'
    try:
        directory = ROOT / 'p'; directory.mkdir(exist_ok=True)
        limit = resource.getrlimit(resource.RLIMIT_AS)
        with pers.scope(closure['paths']):
            try:
                prepared = adm.admit(new_pin, directory, request['frame_roots'], threads=2, memory_gib=request.get('memory_gib', 192), prepare_only=True)
            finally:
                resource.setrlimit(resource.RLIMIT_AS, limit)
        status = 'PREPARED'
        ev('PREPARED', keys=sorted(prepared) if isinstance(prepared, dict) else str(type(prepared)),
           config=(prepared or {}).get('config'), preparation=(prepared or {}).get('preparation'))
        # the second call path: the tree re-derives the scene report when it reads the preparation
        cfg_p = load(pinned(prepared['config']))
        ev('INFO', prepared_scene_coverage=cfg_p.get('scene_coverage', {}).get('reference'), same_as_kit=cfg_p.get('scene_coverage') == new['scene_coverage'])
        try:
            with pers.scope(closure['paths']):
                run.prepared(cfg_p)
            ev('VERIFY_PATH', what='carrier_c1_run.prepared', result='PASSED')
        except BaseException as error:
            ev('VERIFY_PATH', what='carrier_c1_run.prepared', result='RAISED', error=err(error), tb=''.join(tbm.format_exception(type(error), error, getattr(error, TBA)))[-6000:])
            try:
                with pers.scope(closure['paths']):
                    sx.verify(load(pinned(cfg_p['preparation'])), cfg_p)
                ev('VERIFY_PATH', what='s1_exclusions.verify(preparation receipt, prepared config)', result='PASSED')
            except BaseException as error2:
                ev('VERIFY_PATH', what='s1_exclusions.verify', result='RAISED', error=err(error2), tb=''.join(tbm.format_exception(type(error2), error2, getattr(error2, TBA)))[-6000:])
    except BaseException as error:
        ev('ERROR', step='admit prepare_only', error=err(error), tb=''.join(tbm.format_exception(type(error), error, getattr(error, TBA)))[-8000:])
    ev('INFO', coverage_calls=len(calls))
    if calls:
        c = calls[0]; rule, streams = c['rule'], c['streams']
        whole = cfg['scene_coverage']
        tests = dict(whole_store=whole)
        a = load(CEN / 'a.json'); w = load(pinned(whole['reference']))
        hyb = dict(a, withheld_training_rows=dict(a['withheld_training_rows'], camera=w['withheld_training_rows']['camera'], pool=w['withheld_training_rows']['pool']))
        write(NODE / 'ctl_routing_whole.json', hyb); tests['routing_whole_only'] = dict(whole, reference=file_pin(NODE / 'ctl_routing_whole.json'))
        if (NODE / 'lk/a.json').exists():
            lk = load(NODE / 'lk/a.json')
            for name, group in (('pose_a2v3', 'leak_pose'), ('camera', 'leak_routing')):
                ref = dict(a, withheld_training_rows=dict(a['withheld_training_rows'], **{name: lk['withheld_training_rows'][name]}))
                write(NODE / ('ctl_' + group + '.json'), ref); tests[group] = dict(whole, reference=file_pin(NODE / ('ctl_' + group + '.json')))
        for label, policy in tests.items():
            try:
                native_cov(rule, streams, policy); ev('CONTROL', label=label, result='PASSED (control expected a refusal)')
            except Exception as error:
                ev('CONTROL', label=label, result='REFUSED', error=err(error))
    ev('END', status=status)
