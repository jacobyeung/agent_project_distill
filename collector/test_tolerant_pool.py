"""CPU-only fixtures retain all state under DATA; no network, GPUs or deletion."""
from __future__ import annotations

import base64
import contextlib
import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from pool_harness.atomicfs import LockTimeout, StateError, link_lock, publish_json_exclusive, read_json
from pool_harness.pool import PoolController, WorkerLoop
from pool_harness.state import ClaimOutcome, Episode, EpisodeCatalog, EpisodeQueue, PoolConfig, Target, TargetStore
from trace_archive import Archive, install_archive

DATA = Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917')


@pytest.fixture
def root():
    path = DATA / 'runtime_control/gt_teacher_r1313/r1314_fixtures' / uuid.uuid4().hex
    path.mkdir(parents=True)
    return path


def make_queue(root, cap=64, count=128):
    config = PoolConfig('fixture', 1024, spawn_stagger_seconds=.001,
                        heartbeat_seconds=.01, max_owners_per_shard=1024)
    target = TargetStore(root, config)
    target.write(Target(cap, max(1, cap)))
    catalog = EpisodeCatalog([Episode(f'q{i}', 'scene', {'row': {'id': f'q{i}'}}) for i in range(count)])
    queue = EpisodeQueue(root, catalog, target, lambda item: (root / 'done' / item.episode_id).exists())
    return target, queue


@pytest.mark.parametrize('cap,count', [(16, 128), (64, 128), (64, 1)])
def test_64_concurrent_claimants_no_deaths_double_claims_or_cap_excess(root, cap, count):
    target, queue = make_queue(root, cap=cap, count=count)
    barrier = threading.Barrier(64)
    def claim(slot):
        barrier.wait(timeout=20)
        return queue.claim_next(f'worker{slot}', slot)
    with ThreadPoolExecutor(max_workers=64) as executor:
        results = list(executor.map(claim, range(64)))
    claimed = [result.episode.episode_id for result in results if result.outcome is ClaimOutcome.CLAIMED]
    assert len(claimed) == len(set(claimed)) == min(cap, count)
    assert sum(result.outcome is ClaimOutcome.RETIRE for result in results) == 64 - cap
    assert len(list(queue.claim_root.glob('*.json'))) == min(cap, count)


def test_scan_outside_cap_and_recheck_capacity_at_publication(root, monkeypatch):
    target, queue = make_queue(root, count=1)
    real_lock = target.cap_lock
    inside = False
    @contextlib.contextmanager
    def cap_lock():
        nonlocal inside
        with real_lock():
            inside = True
            try: yield
            finally: inside = False
    monkeypatch.setattr(target, 'cap_lock', cap_lock)
    def scan(_item):
        assert not inside
        target.write(Target(0, 1))
        return False
    queue.valid_trace = scan
    assert queue.claim_next('worker', 0).outcome is ClaimOutcome.RETIRE
    assert not list(queue.claim_root.glob('*.json'))


def test_real_lock_timeout_retries_and_worker_telemetry(root, monkeypatch):
    target, queue = make_queue(root)
    ready, release = threading.Event(), threading.Event()
    def holder():
        with target.cap_lock():
            ready.set()
            assert release.wait(10)
    thread = threading.Thread(target=holder)
    thread.start()
    assert ready.wait(10)
    monkeypatch.setattr(target, 'cap_lock', lambda: link_lock(target.lock_dir, 'POOL_CAP', timeout_seconds=.01))
    import pool_harness.state as state
    monkeypatch.setattr(state.random, 'uniform', lambda _lo, _hi: 1)
    # Release after a real timeout; the real backoff remains in effect.
    timer = threading.Timer(.1, release.set)
    timer.start()
    result = queue.claim_next('worker', 0)
    thread.join(10); timer.join(10)
    assert result.outcome is ClaimOutcome.CLAIMED
    events = [read_json(p) for p in (root / 'worker_telemetry/worker').glob('*.json')]
    assert events and all(1 <= row['backoff_seconds'] <= 5 for row in events)


def test_lock_retry_limit_and_non_timeout_errors(root, monkeypatch):
    target, queue = make_queue(root)
    @contextlib.contextmanager
    def timeout():
        raise LockTimeout('injected cap contention')
        yield
    monkeypatch.setattr(target, 'cap_lock', timeout)
    import pool_harness.state as state
    delays = []
    monkeypatch.setattr(state, 'time', SimpleNamespace(monotonic_ns=time.monotonic_ns, time_ns=time.time_ns, sleep=delays.append))
    with pytest.raises(LockTimeout): queue.claim_next('worker', 0)
    assert len(delays) == 20 and all(1 <= delay <= 5 for delay in delays)
    assert len(list((root / 'worker_telemetry/worker').glob('*.json'))) == 21
    @contextlib.contextmanager
    def corrupt():
        raise StateError('corrupt target')
        yield
    monkeypatch.setattr(target, 'cap_lock', corrupt)
    with pytest.raises(StateError, match='corrupt target'): queue.claim_next('other', 1)
    assert not (root / 'worker_telemetry/other').exists()


class Process:
    serial = 1000
    def __init__(self, *_args, **_kwargs):
        Process.serial += 1
        self.pid = Process.serial
        self.returncode = None
        self.terminated = False
        self.waited = False
    def poll(self): return self.returncode
    def terminate(self): self.terminated = True; self.returncode = -15
    def wait(self, timeout=None): self.waited = True; return self.returncode


def controller(root, cap=64, count=128):
    target, queue = make_queue(root, cap=cap, count=count)
    control = PoolController(queue, target, run_epoch='test', command_factory=lambda *a: ['fixture'],
                             log_root=root / 'logs', popen_factory=Process)
    return control, queue


def fail(control, slot=0, claim=True):
    active = control.active[slot]
    result = control.queue.claim_next(active.worker_id, slot) if claim else None
    publish_json_exclusive(control.queue.state_root / 'worker_errors' / f'{active.worker_id}.json',
                           {'exception_type': 'RuntimeError', 'message': 'injected rc=1', 'body': 'complete error'})
    control.queue.publish_exit_receipt(active.worker_id, reason='worker_error', slot=slot, return_code=1)
    active.process.returncode = 1
    return active, result


def test_controller_requeues_rc1_and_spawns_replacement(root):
    control, queue = controller(root)
    control.tick(0)
    failed, claim = fail(control)
    status = control.tick(1)
    assert not status['blocked'] and control.active[0].worker_id != failed.worker_id
    assert not claim.claim_path.exists()
    assert list((root / 'claims/.retired').rglob(claim.claim_path.name))
    assert list((root / 'orphan_recoveries').glob('*.json'))
    receipt = read_json(root / 'worker_failures' / f'{failed.worker_id}.json')
    assert receipt['error']['body'] == 'complete error'
    assert queue.claim_next(control.active[0].worker_id, 0).episode == claim.episode
    control.stop()


def test_three_question_strikes_block_and_survive_restart(root):
    control, queue = controller(root)
    control.tick(0)
    for index in range(3):
        fail(control)
        status = control.tick(index + 1)
        assert bool(status['blocked']) == (index == 2)
    receipt = read_json(root / 'BLOCKED.json')
    assert receipt['reason'] == 'question_infrastructure_three_strikes'
    assert receipt['question_failure_counts'] == {'q0': 3}
    assert not control.active
    restarted = PoolController(queue, control.target_store, run_epoch='restart', command_factory=lambda *a: ['fixture'],
                               log_root=root / 'logs', popen_factory=Process)
    assert restarted.tick(10)['blocked'] == receipt and not restarted.active


def test_failure_storm_strictly_over_half_stops_owned_workers(root):
    control, _ = controller(root, cap=4)
    for i in range(4): control.tick(i)
    for slot in (0, 1): fail(control, slot, claim=False)
    status = control.tick(5)
    assert not status['blocked']  # exactly 50% is permitted
    survivor = control.active[3].process
    fail(control, 2, claim=False)
    status = control.tick(6)
    assert status['blocked']['reason'] == 'worker_failure_storm'
    assert survivor.terminated and survivor.waited and not control.active


def test_old_failures_expire_from_five_minute_window(root, monkeypatch):
    control, _ = controller(root, cap=4)
    control.tick(0)
    fail(control, claim=False)
    control.tick(1)
    import pool_harness.pool as pool
    now = time.time_ns()
    monkeypatch.setattr(pool, 'time', SimpleNamespace(time_ns=lambda: now + 301_000_000_000, monotonic=time.monotonic))
    fail(control, claim=False)
    status = control.tick(2)
    assert not status['blocked']
    control.stop()


def test_recovery_still_refuses_foreign_owner_live_owner_and_complete(root):
    _, queue = make_queue(root)
    claim = queue.claim_next('owner', 0)
    for owner, alive, message in [('foreign', False, 'owner mismatch'), ('owner', True, 'owner is alive')]:
        with pytest.raises(StateError, match=message):
            queue.recover_orphan(claim.episode.episode_id, expected_worker_id=owner,
                                 owner_is_alive=lambda _: alive, proof={'fixture': True})
    (root / 'done').mkdir(); (root / 'done' / claim.episode.episode_id).write_text('terminal')
    with pytest.raises(StateError, match='valid trace'):
        queue.recover_orphan(claim.episode.episode_id, expected_worker_id='owner',
                             owner_is_alive=lambda _: False, proof={'fixture': True})


class TransportError(RuntimeError):
    status_code = 503
    response = SimpleNamespace(status_code=503, content=b'full error body\x00',
                               headers={'Retry-After': '17', 'x-request-id': 'request123'})


@pytest.mark.parametrize('stream', [False, True])
def test_provider_archives_full_error_before_reraise(root, stream):
    class Models:
        def generate_content(self): raise TransportError('unavailable')
        def generate_content_stream(self):
            yield {'chunk': 1}
            raise TransportError('unavailable')
    archive = Archive(root / 'archive', {'fixture': True}, assets_root=root / 'blobs')
    with install_archive(archive, models_cls=Models):
        with pytest.raises(TransportError):
            if stream: list(Models().generate_content_stream())
            else: Models().generate_content()
    events = [read_json(p) for p in sorted(archive.events_dir.glob('*.json'))]
    error = next(row['payload'] for row in events if row['kind'] == 'provider_error')
    assert error['http_status'] == 503 and error['retry_after'] == '17'
    assert error['headers']['x-request-id'] == 'request123'
    assert base64.b64decode(error['body']['data']) == b'full error body\x00'
    assert [row['kind'] for row in events].index('provider_error') < [row['kind'] for row in events].index('provider_terminal')


def test_worker_error_receipt_captures_transport_evidence(root):
    _, queue = make_queue(root)
    def run(*_): raise TransportError('unavailable')
    with pytest.raises(TransportError): WorkerLoop(queue, worker_id='worker', slot=0, run_episode=run).run()
    error = read_json(root / 'worker_errors/worker.json')
    assert error['error']['http_status'] == 503 and error['error']['retry_after'] == '17'
    assert error['episode_id'] == 'q0' and 'TransportError' in error['traceback']


def test_google_stream_error_details_without_response(root):
    from google.genai.errors import ServerError
    from trace_archive import error_details
    body = {'error': {'code': 503, 'message': 'high demand', 'status': 'UNAVAILABLE',
                      'details': [{'reason': 'overloaded'}]}}
    result = error_details(ServerError(503, body))
    assert result['http_status'] == 503 and result['body'] == result['details'] == body


def test_staging_and_retirement_are_outside_cap_lock(root, monkeypatch):
    import pool_harness.atomicfs as atomicfs
    target, queue = make_queue(root)
    real_lock, write_private, retire = target.cap_lock, atomicfs._write_private, atomicfs.retire_path
    inside = False
    @contextlib.contextmanager
    def cap_lock():
        nonlocal inside
        with real_lock():
            inside = True
            try: yield
            finally: inside = False
    def stage(*args, **kw):
        assert not inside
        return write_private(*args, **kw)
    def retire_outside(*args, **kw):
        assert not inside
        return retire(*args, **kw)
    monkeypatch.setattr(target, 'cap_lock', cap_lock)
    monkeypatch.setattr(atomicfs, '_write_private', stage)
    monkeypatch.setattr(atomicfs, 'retire_path', retire_outside)
    assert queue.claim_next('worker', 0).outcome is ClaimOutcome.CLAIMED


def test_collect_start_survives_failure_and_finishes(root, monkeypatch):
    import collect
    target, queue = make_queue(root, cap=4, count=1)
    original_controller = PoolController
    instances = []
    class InjectedController(original_controller):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw, popen_factory=Process)
            self.steps = 0
            instances.append(self)
        def tick(self):
            if self.steps == 1: fail(self)
            if self.steps == 2:
                active = self.active[0]
                def finish(item, claim, failed):
                    (root / 'done').mkdir(exist_ok=True)
                    (root / 'done' / item.episode_id).write_text('complete')
                active.process.returncode = WorkerLoop(queue, worker_id=active.worker_id, slot=0, run_episode=finish).run()
            result = super().tick(self.steps * 10)
            self.steps += 1
            return result
    monkeypatch.setattr(collect, 'PoolController', InjectedController)
    monkeypatch.setattr(collect, 'load_config', lambda *a, **k: {'run_root': str(root)})
    monkeypatch.setattr(collect, 'objects', lambda c: (target, queue, 0))
    monkeypatch.setattr(collect, 'heartbeat', lambda c: None)
    monkeypatch.setattr(collect, 'coord_guard', lambda c: {'last_heartbeat': collect.datetime.now(collect.timezone.utc).isoformat()})
    monkeypatch.setattr(collect.signal, 'signal', lambda *a: None)
    monkeypatch.setattr(collect, 'time', SimpleNamespace(monotonic=time.monotonic, sleep=lambda _: None))
    assert collect.start(SimpleNamespace(config=root / 'config.json', workers=4)) == 0
    assert instances[0].failures and not instances[0].blocked


def test_watchdog_preserves_block_and_does_not_restart_controller(root, monkeypatch):
    import collect
    target, queue = make_queue(root, cap=4)
    monkeypatch.setattr(collect, 'load_config', lambda *a, **k: {'run_root': str(root)})
    monkeypatch.setattr(collect, 'objects', lambda c: (target, queue, 0))
    monkeypatch.setattr(collect.signal, 'signal', lambda *a: None)
    processes = []
    def spawn(*a, **kw):
        proc = Process(); proc.returncode = 1; processes.append(proc); return proc
    monkeypatch.setattr(collect.subprocess, 'Popen', spawn)
    args = SimpleNamespace(config=root / 'config.json', workers=64)
    assert collect.watchdog(args) == 1
    assert len(processes) == 1 and processes[0].waited
    assert target.read().total_workers == 64
    publish_json_exclusive(root / 'BLOCKED.json', {'reason': 'fixture'})
    with pytest.raises(RuntimeError, match='durable BLOCKED'): collect.watchdog(args)
    assert len(processes) == 1


def test_direct_start_cannot_duplicate_an_existing_controller(root, monkeypatch):
    import collect
    monkeypatch.setattr(collect, 'load_config', lambda *a, **k: {'run_root': str(root)})
    entered, release = threading.Event(), threading.Event()
    def running(*_):
        entered.set()
        assert release.wait(10)
        return 0
    monkeypatch.setattr(collect, '_start', running)
    args = SimpleNamespace(config=root / 'config.json', workers=64)
    with ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(collect.start, args)
        assert entered.wait(10)
        try:
            with pytest.raises(TimeoutError, match='permanent lock busy'): collect.start(args)
        finally:
            release.set()
        assert first.result(timeout=10) == 0


def test_watchdog_alarms_on_stalled_finalized_output(root, monkeypatch):
    import collect
    target, queue = make_queue(root, cap=4)
    monkeypatch.setattr(collect, 'load_config', lambda *a, **k: {'run_root': str(root)})
    monkeypatch.setattr(collect, 'objects', lambda c: (target, queue, 0))
    monkeypatch.setattr(collect.signal, 'signal', lambda *a: None)
    proc = Process()
    monkeypatch.setattr(collect.subprocess, 'Popen', lambda *a, **kw: proc)
    clock = [0]
    def elapsed(_): clock[0] = 1801; proc.returncode = 1
    monkeypatch.setattr(collect, 'time', SimpleNamespace(monotonic=lambda: clock[0], time_ns=time.time_ns, sleep=elapsed))
    assert collect.watchdog(SimpleNamespace(config=root / 'config.json', workers=4)) == 1
    alarm = read_json(root / 'WATCHDOG_ALARM.json')
    assert alarm['seconds_without_finalized_progress'] == 1801 and alarm['finalized'] == 0


def test_binding_preserves_original_identity_and_refuses_foreign(root, monkeypatch):
    import collect
    from audit_package import PARENT_SHA
    # All writes are fixture-local; retain the real bind/equality/publication code.
    monkeypatch.setattr(collect, 'validate_config', lambda c: c)
    monkeypatch.setattr(collect, 'objects', lambda c: (None, SimpleNamespace(catalog=SimpleNamespace(episodes=[1])), 0))
    monkeypatch.setattr(collect, 'verify_source', lambda c: {'parent_source_contract': {'sha256': PARENT_SHA}})
    registry = root / 'registry.json'; registry.write_text('{}')
    args = SimpleNamespace(run_root=root / 'run', assets_registry=registry, contract=root / 'new_contract.json',
        contract_sha256='a' * 64, work_id='original_work', agent_id='original_owner', budget=16384,
        episode_limit=0, output=root / 'config1.json')
    original = {'schema': 'r1313-run-identity-v1', 'source_contract_sha256': PARENT_SHA,
        'work_id': args.work_id, 'agent_id': args.agent_id, 'membership_sha256': __import__('training_assets').MEMBERSHIP_SHA}
    publish_json_exclusive(args.run_root / 'RUN_IDENTITY.json', original)
    before = (args.run_root / 'RUN_IDENTITY.json').read_bytes()
    assert collect.bind(args) == 0
    config = read_json(args.output)
    assert config['schema'] == 'r1313-collection-config-v1'
    assert config['collector_version'] == 'r1315-tolerant-sparse-v1'
    assert config['source_contract_sha256'] == 'a' * 64
    assert (args.run_root / 'RUN_IDENTITY.json').read_bytes() == before
    args.agent_id = 'foreign'; args.output = root / 'foreign.json'
    with pytest.raises(ValueError, match='another source/owner'): collect.bind(args)


def test_production_root_check_and_old_config_schema(root, monkeypatch):
    import collect
    monkeypatch.setattr(collect, 'verify_source', lambda c: {})
    monkeypatch.setattr(collect, 'coord_guard', lambda c: {})
    monkeypatch.setattr(collect, 'registry_rows', lambda c: {})
    registry = root / 'registry.json'; registry.write_text('{}')
    config = {'schema': 'r1313-collection-config-v1', 'mode': 'production',
              'run_root': str(DATA / 'collection_gt_r1313'), 'episode_limit': 0,
              'assets_registry': str(registry), 'assets_registry_sha256': collect.sha(registry)}
    assert collect.validate_config(config) == config
    with pytest.raises(ValueError, match='production run root is fixed'):
        collect.validate_config(dict(config, run_root=str(root)))


def test_protected_files_and_identity_comparison_remain_exact():
    import ast
    from audit_package import HERE, PARENT_ROOT, byte_identity
    evidence = byte_identity()
    assert len(evidence['unchanged_files']) == 32
    def comparison(root):
        tree = ast.parse((root / 'collect.py').read_text())
        bind = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'bind')
        return [ast.dump(node, include_attributes=False) for node in ast.walk(bind)
                if isinstance(node, ast.Compare) and 'read_json' in ast.unparse(node)]
    assert comparison(HERE) == comparison(PARENT_ROOT)
