import sys, os, runpy, types, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *
limits()
name, job = sys.argv[1:3]
root = Path(os.environ['TEST_ROOT'])
project = Path(NROOT)
sys.path[:0] = [str(KIT/'b'), str(TREE)]
result = dict(case=name, assertions=[], target_files=[])

def check(label, value, **details):
    result['assertions'].append(dict(assertion=label, pass_=bool(value), **details))

def native():
    from student_pilot.carrier_c1_run import identity
    from launch_r1.entry import ASSERTIONS
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    check('runtime has at most four threads', len(list(Path('/proc/self/task').iterdir())) <= 4)
    return identity, ASSERTIONS

def fixture():
    identity, assertions = native()
    p = root/'p'
    sources, streams, stores = {}, {}, {}
    for stream in STREAMS:
        population = put(p/'inputs'/f'{stream}.json', [{'id': 1}, {'id': 2}])
        stream_pin = put(p/'inputs'/f'{stream}-receipt.json', dict(count=2, database=population))
        streams[stream] = stream_pin
        sources[stream] = [dict(receipt=stream_pin, population=population, count=2)]
        stores[stream] = dict(count=2, database=population)
    prep = put(p/'prepared.json', dict(streams=stores, r1_training={}))
    cfg = dict(contract_epoch=False, world_size=4, streams=streams,
               remove_files=[put(p/'inputs/remove.json', [])], preparation=prep,
               r1_training=dict(proof_mode='train', init_policy='step400_export_weights_fresh_v1'))
    if name == 'h_no_policy':
        cfg['r1_training'] = dict(proof_mode='q')
    value = identity(cfg)
    source_pin = put(p/'q/ss.json', sources)
    staging = put(p/'i/staging.json', dict(entries={'ss.json': dict(sha256=source_pin['sha256'], bytes=(p/'q/ss.json').stat().st_size)}))
    host = dict(status='PASS', config_identity=value, assertions=dict.fromkeys(assertions, True),
                loader_audit=dict(complete=True), staging_plan_sha256=staging['sha256'])
    live = project/'o'/job/'live'
    live.mkdir(parents=True)
    rows = {}
    for stream in STREAMS:
        keys = put(live/f'{stream}-keys.json', [])
        rows[stream] = dict(config_identity=value, store_pins=stores[stream], source_pins=sources[stream],
                            protected_keys=dict(file=f'{stream}-keys.json', sha256=keys['sha256'], count=0),
                            status='PASS', result=dict(stream=stream, protected_rows=0, admitted_rows=2, source_rows=2),
                            refusals=[], counts=dict(source=2, admitted=2))
    census = put(root/'c5.json', dict(schema='r1-protected-census-v1', phase='final', config_identity=value, streams=rows))
    raw(live/'c4.json', (root/'c5.json').read_bytes())
    host['protected_census'] = census
    host_pin = put(p/'q/host.json', host)
    if name.startswith('rv_'):
        cfg['r1_training']['host_receipt'] = host_pin
        raw(live/'h0.json', (p/'q/host.json').read_bytes())
        prepared = load(p/'prepared.json')
        prepared['r1_training'] = cfg['r1_training']
        cfg['preparation'] = put(p/'prepared.json', prepared)
    config_pin = put(p/'cfg.json', cfg)
    if name == 'h_bad_host':
        host_pin = dict(host_pin, sha256='0'*64)
    put(p/'q/RESULT.json', dict(status='ADMIT', init_milestone=400, config=config_pin, host_receipt=host_pin))
    put(root/'rooms.json', {})
    result['fixture'] = dict(config=config_pin, config_identity=value, host=host_pin, census=census)
    return cfg, value, identity, live

def h_case():
    cfg, value, identity, live = fixture()
    expected = {'h_no_policy': 'E85', 'h_bad_host': 'R1_HOST_RECEIPT_INVALID'}.get(name)
    sys.argv = [str(KIT/'b/h.py'), str(root/'p'), str(root/'p/v.json')]
    error = None
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    except ValueError as e:
        error = str(e)
    result.update(target_files=['b/h.py'], target_exit_code=1 if error else 0, refusal=error)
    if expected:
        check('named refusal', error == expected, expected=expected, observed=error)
        check('no prepared output on refusal', not (root/'p/v.json').exists())
    else:
        check('successful h.py execution', error is None, observed=error)
        out = load(root/'p/v.json')
        host = load(out['r1_training']['host_receipt']['path'])
        prep = load(out['preparation']['path'])
        check('identity unchanged', identity(out) == value)
        check('host pin authenticates', sha(Path(out['r1_training']['host_receipt']['path'])) == out['r1_training']['host_receipt']['sha256'])
        check('host and census bound', host['config_identity'] == value and host['protected_census'] == result['fixture']['census'])
        check('preparation pin authenticates', sha(Path(out['preparation']['path'])) == out['preparation']['sha256'])
        check('preparation carries host binding', prep['r1_training'] == out['r1_training'])
        check('published host matches bound receipt', sha(live/'h0.json') == out['r1_training']['host_receipt']['sha256'])

def rd_case():
    from z import screen, load as capsule
    raw(root/'q.log', 'tiny routing fixture\n')
    put(root/'p/r0.json', dict(status='ADMIT'))
    if name != 'rd_missing':
        put(root/'p/routing_selection.json', dict(schema='synthetic-selection', selected=[1, 2]))
    requested_job = 'invalid/job' if name == 'rd_bad_job' else job
    sys.argv = [str(KIT/'b/rd.py'), str(root), requested_job, '0']
    error = None
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    except ValueError as e:
        error = str(e)
    result.update(target_files=['b/rd.py'], target_exit_code=1 if error else 0, refusal=error)
    expected = {'rd_missing': 'R1_ROUTING_SELECTION_MISSING', 'rd_bad_job': 'R1_ROUTING_JOB_ID_REQUIRED'}.get(name)
    check('return status and refusal', error == expected, expected=expected, observed=error)
    target = project/'o'/job
    if name == 'rd_bad_job':
        check('invalid job publishes nothing', not (project/'o').exists())
        return
    receipt = load(target/'r1.json')
    check('r1 status records producer returncode', receipt['returncode'] == 0)
    expected_files = ['q.log', 'r0.json'] + ([] if name == 'rd_missing' else ['routing_selection.json'])
    check('manifest file set', set(receipt['files']) == set(expected_files))
    published = {}
    for leaf in expected_files:
        source = root/'q.log' if leaf == 'q.log' else root/'p'/leaf
        expected_bytes = screen(source.read_text(), capsule(KIT/'k/g.json'), capsule(KIT/'b/wh.json')).encode() if leaf == 'q.log' else source.read_bytes()
        actual = (target/leaf).read_bytes()
        check('published hash and byte count: '+leaf, actual == expected_bytes and len(actual) == receipt['files'][leaf])
        published[leaf] = dict(sha256=sha(target/leaf), bytes=len(actual))
    result['published'] = published
    result['receipt_schema_note'] = 'Final rd.py r1.json records returncode and byte counts; this test independently verifies published SHA256 values.'

def rv_case():
    cfg, value, identity, live = fixture()
    import rv
    from z import load as capsule, seal
    check('final kit seal', seal(KIT) == '60d24119d5844d9b89376e340a5d2f0ef86ec9edd31247dd5af0bb60b936d19c')
    bound = capsule(KIT/'k/a.json')['review_wait_seconds']
    class Clock:
        value = 1000.0
        sleeps = []
        def monotonic(self): return self.value
        def sleep(self, seconds):
            self.sleeps.append(seconds)
            self.value += bound+1
    clock = Clock()
    rv.time = clock
    # The requested coverage starts after WAITING_REVIEW. Keep identity, census,
    # receipt parsing, permission checks and preparation sync real; bypass only
    # native row sampling, which explicitly asks Torch for eight threads.
    def evidence_stub(*args):
        result['evidence_stub_called'] = True
        return dict(fixture=True)
    rv.evidence = evidence_stub
    review = project/'n_r/review.json'
    review.parent.mkdir(mode=0o700)
    if name != 'rv_absent':
        receipt = dict(verdict='FAIL' if name == 'rv_notpass' else 'PASS',
                       config_identity='0'*64 if name == 'rv_identity' else value)
        if name == 'rv_malformed': raw(review, '{ malformed json')
        else: put(review, receipt)
        review.chmod(0o644 if name == 'rv_mode' else 0o600)
    config = root/'p/cfg.json'
    before = sha(config)
    rc = rv.run(KIT, root, config, job, interval=0.01)
    result.update(target_files=['b/rv.py'], target_exit_code=rc,
                  wait=dict(sealed_bound_seconds=bound, interval_seconds=0.01,
                            fake_clock_advance_seconds=bound+1, sleeps=clock.sleeps),
                  limitations=['Only rv.evidence is stubbed; the wait and receipt branches execute unchanged final source.'])
    check('WAITING_REVIEW reached', (live/'WAITING_REVIEW.json').exists())
    waiting = load(live/'WAITING_REVIEW.json')
    check('waiting identity matches config', waiting['identity'] == value and waiting['v_sha256'] == before)
    if name == 'rv_pass':
        check('accepted exit zero', rc == 0)
        accepted = load(live/'REVIEW_ACCEPTED.json')
        check('acceptance binds identity and receipt', accepted['identity'] == value and accepted['review_sha256'] == sha(review))
        out = load(config)
        check('identity unchanged after acceptance', identity(out) == value)
        pin = out['r1_training']['review']
        check('review pinned locally', pin['sha256'] == sha(review) == sha(Path(pin['path'])))
        check('preparation binds review', load(out['preparation']['path'])['r1_training'] == out['r1_training'])
        check('no refusal', not (live/'REVIEW_REFUSED.json').exists())
    else:
        expected = dict(rv_absent='R1_REVIEW_TIMEOUT', rv_identity='R1_REVIEW_IDENTITY_DIFFERS',
                        rv_malformed='R1_REVIEW_FILE_UNUSABLE', rv_notpass='R1_REVIEW_NOT_PASS',
                        rv_mode='R1_REVIEW_FILE_UNUSABLE')[name]
        refusal = load(live/'REVIEW_REFUSED.json')['refusal']
        result['refusal'] = refusal
        check('named review refusal', rc == 1 and refusal == expected, expected=expected, observed=refusal)
        check('no acceptance', not (live/'REVIEW_ACCEPTED.json').exists())
        check('config unchanged on refusal', sha(config) == before)
        if name == 'rv_absent': check('timeout follows a poll and sleep', clock.sleeps == [0.01])

try:
    if name.startswith('h_'): h_case()
    elif name.startswith('rd_'): rd_case()
    elif name.startswith('rv_'): rv_case()
    else: raise ValueError(name)
except Exception as e:
    result['unexpected_error'] = traceback.format_exc()
    check('fixture and assertions complete', False, error=str(e))
result['verdict'] = 'PASS' if all(v['pass_'] for v in result['assertions']) else 'FAIL'
put(root.parent/'case_result.json', result)
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result['verdict'] == 'PASS' else 1)
