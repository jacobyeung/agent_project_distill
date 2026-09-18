"""CPU-only fixtures retain all state under DATA; no network, GPUs or deletion."""
from __future__ import annotations

import base64
import contextlib
import errno
import hashlib
import json
import os
import multiprocessing
import threading
import tempfile
import unittest
from unittest.mock import patch
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from pool_harness.atomicfs import LockTimeout, StateError, link_lock, publish_json_exclusive, read_json
from pool_harness.pool import PoolController, WorkerLoop
from pool_harness.state import ClaimOutcome, Episode, EpisodeCatalog, EpisodeQueue, PoolConfig, Target, TargetStore
from trace_archive import Archive, install_archive, _snapshot_name

DATA = Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917')


@pytest.fixture
def root():
    path = Path(os.environ.get('REMEDIATION_FIXTURE_ROOT', str(DATA / 'runtime_control/gt_teacher_r1313/r1314_fixtures'))) / uuid.uuid4().hex
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


def _process_claim(root, cap, count, slot):
    config = PoolConfig('fixture', 1024, max_owners_per_shard=1024)
    target = TargetStore(root, config)
    catalog = EpisodeCatalog([Episode(f'q{i}', 'scene', {'row': {'id': f'q{i}'}}) for i in range(count)])
    queue = EpisodeQueue(root, catalog, target, lambda item: False)
    (root / f'ready_{slot}').write_text(str(os.getpid()))
    deadline = time.monotonic() + 60
    while not (root / 'GO').exists():
        if time.monotonic() > deadline: raise RuntimeError('claim barrier deadline')
        time.sleep(.01)
    result = queue.claim_next(f'worker{slot}', slot)
    publish_json_exclusive(root / 'results' / f'{slot}.json',
                           {'pid': os.getpid(), 'outcome': result.outcome.value,
                            'episode_id': result.episode.episode_id if result.episode else None})


@pytest.mark.parametrize('cap,count', [(16, 128), (64, 128), (64, 1)])
def test_64_concurrent_claimants_no_deaths_double_claims_or_cap_excess(root, cap, count):
    target, queue = make_queue(root, cap=cap, count=count)
    context = multiprocessing.get_context('fork')
    processes = [context.Process(target=_process_claim, args=(root, cap, count, slot)) for slot in range(64)]
    for process in processes: process.start()
    try:
        deadline = time.monotonic() + 60
        while len(list(root.glob('ready_*'))) < 64:
            assert time.monotonic() < deadline
            time.sleep(.01)
        assert all(process.is_alive() for process in processes)
        (root / 'GO').write_text('claim')
        while any(process.is_alive() for process in processes):
            assert time.monotonic() < deadline
            for process in processes: process.join(timeout=.01)
        assert all(process.exitcode == 0 for process in processes)
        results = [read_json(path) for path in (root / 'results').glob('*.json')]
        assert len(results) == len({row['pid'] for row in results}) == 64
        claimed = [row['episode_id'] for row in results if row['outcome'] == ClaimOutcome.CLAIMED.value]
        assert len(claimed) == len(set(claimed)) == min(cap, count)
        assert sum(row['outcome'] == ClaimOutcome.RETIRE.value for row in results) == 64 - cap
        assert len(list(queue.claim_root.glob('*.json'))) == min(cap, count)
    finally:
        for process in processes:
            if process.is_alive(): process.terminate()
            process.join(timeout=2)


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
    import pool_harness.atomicfs as atomicfs
    import pool_harness.state as state
    clock = [0.0]
    held = target.cap_lock()
    held.__enter__()
    released = [False]
    delays = []
    def backoff(delay):
        delays.append(delay)
        held.__exit__(None, None, None)
        released[0] = True
    monkeypatch.setattr(atomicfs, 'time', SimpleNamespace(monotonic=lambda: clock[0], sleep=lambda n: clock.__setitem__(0, clock[0]+n)))
    monkeypatch.setattr(state, 'time', SimpleNamespace(monotonic_ns=time.monotonic_ns, time_ns=time.time_ns, sleep=backoff))
    monkeypatch.setattr(target, 'cap_lock', lambda: link_lock(target.lock_dir, 'POOL_CAP', timeout_seconds=.01))
    try:
        result = queue.claim_next('worker', 0)
    finally:
        if not released[0]: held.__exit__(None, None, None)
    assert result.outcome is ClaimOutcome.CLAIMED
    events = [read_json(p) for p in (root / 'worker_telemetry/worker').glob('*.json')]
    assert len(events) == len(delays) == 1
    assert 1 <= events[0]['backoff_seconds'] <= 5


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


@pytest.mark.parametrize('age_ns,blocked', [(299_999_999_999, True), (300_000_000_000, True), (300_000_000_001, False)])
def test_old_failures_expire_from_five_minute_window(root, monkeypatch, age_ns, blocked):
    import pool_harness.pool as pool
    now = [1_000_000_000_000]
    monkeypatch.setattr(pool, 'time', SimpleNamespace(time_ns=lambda: now[0], monotonic=time.monotonic))
    control, _ = controller(root, cap=4)
    control.tick(0)
    fail(control, claim=False)
    control.tick(1)
    now[0] += age_ns
    fail(control, claim=False)
    control.tick(2)
    fail(control, claim=False)
    status = control.tick(3)
    assert len(control.failure_events) == 3
    assert bool(status['blocked']) is blocked
    if blocked: assert status['blocked']['reason'] == 'worker_failure_storm'
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


@pytest.mark.parametrize('exhausted', [False, True])
def test_orphan_recovery_contention_is_bounded_and_counts_failure_once(root, monkeypatch, exhausted):
    import pool_harness.pool as pool
    control, queue = controller(root)
    control.tick(0)
    failed, claim = fail(control)
    real = queue.recover_orphan
    calls, delays = [], []
    def recover(*args, **kwargs):
        calls.append(args)
        if exhausted or len(calls) <= 2: raise LockTimeout('injected recovery contention')
        return real(*args, **kwargs)
    monkeypatch.setattr(queue, 'recover_orphan', recover)
    monkeypatch.setattr(pool, 'time', SimpleNamespace(time_ns=time.time_ns, monotonic=time.monotonic, sleep=delays.append))
    status = control.tick(1)
    assert len(calls) == 3 and delays == [1, 2]
    assert len(control.failure_events) == len(list((root/'worker_failures').glob('*.json'))) == 1
    assert bool(status['blocked']) is exhausted
    if exhausted:
        assert status['blocked']['reason'] == 'orphan_recovery_contention_exhausted'
        assert claim.claim_path.exists() and not control.active
        assert len(list((root/'recovery_failures').glob('*.json'))) == 3
    else:
        assert not claim.claim_path.exists()
        assert control.active[0].worker_id != failed.worker_id
    control.stop()


def test_recovery_resume_after_publication_and_after_retirement(root, monkeypatch):
    import pool_harness.pool as pool
    control, queue = controller(root)
    control.tick(0)
    failed, claim = fail(control)
    real = queue.recover_orphan
    calls = []
    def interrupted(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1: raise RuntimeError('controller interrupted after failure receipt')
        result = real(*args, **kwargs)
        if len(calls) == 2: raise LockTimeout('completion uncertain after retirement')
        return result
    monkeypatch.setattr(queue, 'recover_orphan', interrupted)
    monkeypatch.setattr(pool, 'time', SimpleNamespace(time_ns=time.time_ns, monotonic=time.monotonic, sleep=lambda _: None))
    with pytest.raises(RuntimeError, match='controller interrupted'): control._reap()
    original = (root/'worker_failures'/f'{failed.worker_id}.json').read_bytes()
    control._reap()
    assert len(calls) == 3 and len(control.failure_events) == 1
    assert (root/'worker_failures'/f'{failed.worker_id}.json').read_bytes() == original
    assert not claim.claim_path.exists()
    assert len(list((root/'orphan_recoveries').glob('*.json'))) == 1
    control.stop()


@pytest.mark.parametrize('terminal', ['wrong_answer', 'budget_cutoff'])
def test_worker_failure_preserves_merit_terminals_and_attempt_bytes(root, terminal):
    control, queue = controller(root)
    control.tick(0)
    active, claim = fail(control)
    (root/'done').mkdir()
    final = root/'done'/claim.episode.episode_id
    final.write_text(terminal)
    attempt = root/'attempt.json'; attempt.write_text('{"provider_started":true}')
    before = claim.claim_path.read_bytes(), final.read_bytes(), attempt.read_bytes()
    control.tick(1)
    assert (claim.claim_path.read_bytes(), final.read_bytes(), attempt.read_bytes()) == before
    assert not list((root/'orphan_recoveries').glob('*.json'))
    assert control.failure_events[0]['question_ids'] == []
    control.stop()


@pytest.mark.parametrize('entry', ['start', '_start', 'controller', 'watchdog'])
def test_controller_death_with_surviving_worker_refuses_every_start(root, monkeypatch, entry):
    import collect
    import subprocess
    import sys
    target, queue = make_queue(root/'pool_b16384')
    code = '''
import os,sys,time
from pathlib import Path
from pool_harness.state import HeartbeatStore
root=Path(sys.argv[1]);HeartbeatStore(root).publish('predecessor',state='running',episode_id=None)
while not (root/'worker_stop').exists():time.sleep(.01)
'''
    worker = subprocess.Popen([sys.executable, '-B', '-c', code, str(target.state_root)])
    try:
        deadline = time.monotonic()+10
        while not queue.heartbeats.path('predecessor').exists():
            assert time.monotonic()<deadline
            time.sleep(.01)
        # A predecessor controller dies and releases its real kernel lock.
        predecessor = subprocess.Popen([sys.executable, '-B', '-c',
            "import os,sys; from pathlib import Path; from nondeleting_lifecycle import permanent_lock; "
            "lock=permanent_lock(Path(sys.argv[1])); lock.__enter__(); os._exit(23)",
            str(target.state_root/'CONTROLLER.lock')])
        while predecessor.poll() is None: time.sleep(.01)
        assert predecessor.wait(timeout=2) == 23
        # Expired heartbeat timestamps must not permit a still-live PID.
        hb = read_json(queue.heartbeats.path('predecessor')); hb['wall_time_ns'] = 0
        from pool_harness.atomicfs import replace_json
        replace_json(queue.heartbeats.path('predecessor'), hb)
        config = {'run_root': str(root)}
        monkeypatch.setattr(collect, 'load_config', lambda *a, **k: config)
        monkeypatch.setattr(collect, 'objects', lambda c: (target, queue, 0))
        monkeypatch.setattr(collect.signal, 'signal', lambda *a: None)
        args = SimpleNamespace(config=root/'config', workers=64)
        with pytest.raises(StateError, match='remains live'):
            if entry == '_start': collect._start(args, config)
            elif entry == 'controller':
                PoolController(queue, target, run_epoch='new', command_factory=lambda *a: ['forbidden'], log_root=root/'logs')
            else: getattr(collect, entry)(args)
        assert not (root/'logs').exists()
    finally:
        (target.state_root/'worker_stop').write_text('stop')
        worker.wait(timeout=2)
    queue.require_drained()


@pytest.mark.parametrize('source', ['exception', 'response', 'prior_chunk', 'unavailable'])
def test_provider_error_preserves_served_model_identity(root, source):
    class Models:
        def generate_content(self):
            error = TransportError('unavailable')
            if source == 'exception': error.model_version = 'served-exception'
            if source == 'response': error.response = SimpleNamespace(model_version='served-response')
            raise error
        def generate_content_stream(self):
            yield {'model_version': 'served-stream'} if source == 'prior_chunk' else {'chunk': 1}
            yield {'chunk': 2}
            self.generate_content()
    archive = Archive(root/'archive', {'fixture': True}, assets_root=root/'blobs')
    with install_archive(archive, models_cls=Models):
        with pytest.raises(TransportError): list(Models().generate_content_stream())
    events = [read_json(p) for p in archive.events_dir.glob('*.json')]
    payload = next(e['payload'] for e in events if e['kind'] == 'provider_error' and e['payload']['method'] == 'generate_content_stream')
    assert payload['served_model_status'] == ('unavailable' if source == 'unavailable' else 'available')
    assert {e['value'] for e in payload['served_model_evidence']} == {
        'exception': {'served-exception'}, 'response': {'served-response'},
        'prior_chunk': {'served-stream'}, 'unavailable': set()}[source]


def test_controller_restart_resumes_durable_failure_recovery(root, monkeypatch):
    import subprocess
    import sys
    target, queue = make_queue(root, count=1)
    code = '''
import sys
from pathlib import Path
from pool_harness.state import Episode,EpisodeCatalog,EpisodeQueue,PoolConfig,TargetStore
root=Path(sys.argv[1]);target=TargetStore(root,PoolConfig('fixture',1024))
queue=EpisodeQueue(root,EpisodeCatalog([Episode('q0','scene',{'row':{'id':'q0'}})]),target,lambda _:False)
queue.claim_next(sys.argv[2],0)
sys.exit(1)
'''
    control = PoolController(queue, target, run_epoch='dead_controller',
        command_factory=lambda worker, *_: [sys.executable, '-B', '-c', code, str(root), worker], log_root=root/'logs')
    control.tick(0)
    worker = control.active[0]
    deadline = time.monotonic()+10
    while worker.process.poll() is None:
        assert time.monotonic()<deadline
        time.sleep(.01)
    real = queue.recover_orphan
    def interrupted(*a, **kw): raise RuntimeError('controller death after receipt')
    monkeypatch.setattr(queue, 'recover_orphan', interrupted)
    with pytest.raises(RuntimeError, match='controller death'): control._reap()
    evidence = (root/'worker_failures'/f'{worker.worker_id}.json').read_bytes()
    control.stop()
    monkeypatch.setattr(queue, 'recover_orphan', real)
    successor = PoolController(queue, target, run_epoch='successor', command_factory=lambda *a: ['fixture'],
                               popen_factory=Process, log_root=root/'logs')
    successor.tick(1)
    assert len(successor.failure_events) == 1
    assert (root/'worker_failures'/f'{worker.worker_id}.json').read_bytes() == evidence
    assert not queue.claim_path(queue.catalog.episodes[0]).exists()
    assert (root/'worker_recoveries'/f'{worker.worker_id}.json').exists()
    successor.stop()


@pytest.mark.parametrize('lock_kind', ['POOL_CAP', 'RECOVER'])
def test_recovery_retries_real_link_lock_contention(root, monkeypatch, lock_kind):
    import pool_harness.atomicfs as atomicfs
    import pool_harness.pool as pool
    control, queue = controller(root)
    control.tick(0)
    _, claim = fail(control)
    name = 'POOL_CAP' if lock_kind == 'POOL_CAP' else f'RECOVER_{claim.episode.key}'
    held = link_lock(control.target_store.lock_dir, name)
    held.__enter__()
    released = [False]; delays = []; clock = [0.0]
    monkeypatch.setattr(atomicfs, 'time', SimpleNamespace(monotonic=lambda: clock[0], sleep=lambda n: clock.__setitem__(0,clock[0]+n)))
    def backoff(delay):
        delays.append(delay); held.__exit__(None,None,None); released[0] = True
    monkeypatch.setattr(pool, 'time', SimpleNamespace(time_ns=time.time_ns, monotonic=time.monotonic, sleep=backoff))
    try:
        control._reap()
    finally:
        if not released[0]: held.__exit__(None,None,None)
    assert delays == [1] and len(control.failure_events) == 1
    assert not claim.claim_path.exists() and not control.blocked
    assert len(list((root/'recovery_failures').glob('*.json'))) == 1
    control.stop()


def test_recovery_exhaustion_remains_blocked_on_restart(root, monkeypatch):
    import pool_harness.pool as pool
    control, queue = controller(root)
    control.tick(0); fail(control)
    calls = []
    def contended(*a, **kw): calls.append(1); raise LockTimeout('persistent contention')
    monkeypatch.setattr(queue, 'recover_orphan', contended)
    monkeypatch.setattr(pool, 'time', SimpleNamespace(time_ns=time.time_ns, monotonic=time.monotonic, sleep=lambda _: None))
    control.tick(1)
    before = (root/'BLOCKED.json').read_bytes()
    restarted = PoolController(queue, control.target_store, run_epoch='restart',
        command_factory=lambda *a: ['forbidden'], popen_factory=Process, log_root=root/'logs')
    assert restarted.tick(2)['blocked']['reason'] == 'orphan_recovery_contention_exhausted'
    assert calls == [1,1,1] and not restarted.active
    assert (root/'BLOCKED.json').read_bytes() == before


def test_startup_overlap_refuses_worker_before_first_publication(root):
    import ctypes
    import sys
    from nondeleting_lifecycle import permanent_lock
    target, queue = make_queue(root, cap=1, count=2)
    code = '''
import os,sys,time
from pathlib import Path
from pool_harness.state import Episode,EpisodeCatalog,EpisodeQueue,PoolConfig,TargetStore
root=Path(sys.argv[1]);worker=sys.argv[2]
target=TargetStore(root,PoolConfig('fixture',1024))
queue=EpisodeQueue(root,EpisodeCatalog([Episode('q0','scene',{}),Episode('q1','scene',{})]),target,lambda _:False)
(root/('ready_'+worker)).write_text(str(os.getpid()))
deadline=time.monotonic()+40
while not (root/'GO').exists() and not (root/'STOP').exists():
    assert time.monotonic()<deadline
    time.sleep(.01)
if not (root/'STOP').exists():
    queue.heartbeats.publish(worker,state='claim_boundary',episode_id=None)
    result=queue.claim_next(worker,0)
    (root/('result_'+worker)).write_text(result.episode.episode_id)
    while not (root/'STOP').exists():
        assert time.monotonic()<deadline
        time.sleep(.01)
'''
    def predecessor():
        with permanent_lock(root/'CONTROLLER.lock'):
            control = PoolController(queue, target, run_epoch='predecessor',
                command_factory=lambda worker, *_: [sys.executable, '-B', '-c', code, str(root), worker],
                log_root=root/'logs')
            control.tick(0)
            active = control.active[0]
            publish_json_exclusive(root/'predecessor_worker.json',
                                   {'pid': active.process.pid, 'worker_id': active.worker_id})
            deadline = time.monotonic()+20
            while not (root/f'ready_{active.worker_id}').exists():
                assert time.monotonic()<deadline
                time.sleep(.01)
            os._exit(23)
    libc = ctypes.CDLL(None)
    previous = ctypes.c_int()
    assert libc.prctl(37, ctypes.byref(previous), 0, 0, 0) == 0
    assert libc.prctl(36, 1, 0, 0, 0) == 0
    prior = multiprocessing.get_context('fork').Process(target=predecessor)
    prior.start()
    old = None
    try:
        prior.join(timeout=20)
        assert prior.exitcode == 23
        old = read_json(root/'predecessor_worker.json')
        os.kill(old['pid'], 0)
        assert not list(queue.heartbeats.root.glob('*.json'))
        assert not list(queue.claim_root.glob('*.json'))
        with permanent_lock(root/'CONTROLLER.lock'):
            with pytest.raises(StateError, match='predecessor'):
                queue.require_drained()
            with pytest.raises(StateError, match='predecessor'):
                PoolController(queue, target, run_epoch='successor',
                    command_factory=lambda *_: ['forbidden'], log_root=root/'logs')
        (root/'GO').write_text('release surviving worker')
        deadline = time.monotonic()+20
        while not (root/f"result_{old['worker_id']}").exists():
            assert time.monotonic()<deadline
            time.sleep(.01)
        assert target.read().total_workers == 1
        claims = [read_json(p) for p in queue.claim_root.glob('*.json')]
        assert len(claims) == 1 and claims[0]['worker_id'] == old['worker_id']
        os.kill(old['pid'], 0)
    finally:
        (root/'STOP').write_text('finish fixture worker')
        if prior.is_alive(): prior.terminate()
        prior.join(timeout=20)
        if old is None and (root/'predecessor_worker.json').exists():
            old = read_json(root/'predecessor_worker.json')
        if old:
            deadline = time.monotonic()+20
            while os.waitpid(old['pid'], os.WNOHANG) == (0, 0):
                assert time.monotonic()<deadline
                time.sleep(.01)
        assert libc.prctl(36, previous.value, 0, 0, 0) == 0
    queue.require_drained()


def test_recovery_resume_preserves_replacement_owner_after_retirement(root, monkeypatch):
    import subprocess
    import sys
    target, queue = make_queue(root, count=2)
    code = '''
import sys
from pathlib import Path
from pool_harness.state import Episode,EpisodeCatalog,EpisodeQueue,PoolConfig,TargetStore
root=Path(sys.argv[1]);worker=sys.argv[2]
target=TargetStore(root,PoolConfig('fixture',1024))
queue=EpisodeQueue(root,EpisodeCatalog([Episode('q0','scene',{}),Episode('q1','scene',{})]),target,lambda _:False)
queue.heartbeats.publish(worker,state='claim_boundary',episode_id=None)
assert queue.claim_next(worker,0).episode.episode_id=='q0'
sys.exit(1)
'''
    command = lambda worker, *_: [sys.executable, '-B', '-c', code, str(root), worker]
    control = PoolController(queue, target, run_epoch='failed', command_factory=command, log_root=root/'logs')
    control.tick(0)
    failed = control.active[0]
    assert failed.process.wait(timeout=20) == 1
    real = queue.recover_orphan
    def interrupted(*args, **kwargs):
        real(*args, **kwargs)
        raise RuntimeError('controller death after retirement')
    monkeypatch.setattr(queue, 'recover_orphan', interrupted)
    try:
        with pytest.raises(RuntimeError, match='controller death after retirement'):
            control._reap()
    finally:
        control.stop()
    monkeypatch.setattr(queue, 'recover_orphan', real)
    event_path = root/'worker_failures'/f'{failed.worker_id}.json'
    event_bytes = event_path.read_bytes()
    event = read_json(event_path)
    assert not (root/'worker_recoveries'/f'{failed.worker_id}.json').exists()
    competitor = subprocess.Popen(command('competitor'))
    assert competitor.wait(timeout=20) == 1
    claim_path = queue.claim_path(queue.catalog.episodes[0])
    before = claim_path.read_bytes()
    assert read_json(claim_path)['worker_id'] == 'competitor'
    with pytest.raises(StateError, match='orphan recovery owner mismatch'):
        queue.recover_orphan('q0', expected_worker_id=failed.worker_id,
                            owner_is_alive=lambda _: False, proof={'unrelated': True})
    successor = PoolController(queue, target, run_epoch='restart',
        command_factory=lambda *_: ['fixture'], popen_factory=Process, log_root=root/'logs')
    def unexpected_owner_check(_claim):
        raise AssertionError('completed retirement must not inspect the replacement owner')
    monkeypatch.setattr(successor, '_owner_is_alive', unexpected_owner_check)
    try:
        assert not successor.tick(1)['blocked']
        assert claim_path.read_bytes() == before
        assert event_path.read_bytes() == event_bytes
        assert len(successor.failure_events) == 1
        assert len(list((root/'orphan_recoveries').glob('*.json'))) == 1
        completion = read_json(root/'worker_recoveries'/f'{failed.worker_id}.json')
        assert completion['failure_receipt'] == event['recovery_proof']['failure_receipt']
        assert not (root/'BLOCKED.json').exists()
    finally:
        successor.stop()


def test_monitor_filter_matches_both_collectors_and_episode_children(root):
    import ast
    script = Path(__file__).resolve().parents[1]/'tools/monitor_v5_remediation.py'
    tree = ast.parse(script.read_text())
    boundary = next(i for i, node in enumerate(tree.body) if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'start' for target in node.targets))
    definitions = [node for node in tree.body[:boundary] if not isinstance(node, ast.Expr)]
    namespace = {'__file__': str(script)}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(script), 'exec'), namespace)
    legacy = Path('/home/jjyeung/agent_project_r1313_gt_teacher/agent/rounds/candidates/r1313_vsi_distill_gt_training')
    distill = Path('/home/jjyeung/agent_project_distill/collector')
    attempts = namespace['ROOT']/'attempts'
    rows = {
        101: ['python', '-B', str(legacy/'collect.py'), 'start'],
        102: ['python', '-B', str(legacy/'collect.py'), 'worker'],
        103: ['python', '-B', str(legacy/'run_experiment_r1313.py'), str(attempts/'q0/b16384')],
        201: ['python', '-B', str(distill/'collect.py'), 'start'],
        202: ['python', '-B', str(distill/'collect.py'), 'worker'],
        203: ['python', '-B', str(distill/'run_experiment_r1313.py'), str(attempts/'q1/b16384')],
        301: ['python', '-B', '/other/collect.py', 'worker'],
        302: ['python', '-B', str(distill/'collect.py'), 'readiness'],
        303: ['python', '-B', str(distill/'run_experiment_r1313.py'), '/other/attempts/q0'],
        304: ['python', '-B', str(legacy/'run_experiment_r1313.py'), '/other/attempts/q0'],
        305: ['python', '-B', str(distill/'collect.py.bak'), 'worker'],
    }
    table = root/'proc'
    for pid, args in rows.items():
        entry = table/str(pid)
        entry.mkdir(parents=True)
        (entry/'cmdline').write_bytes(b'\0'.join(arg.encode() for arg in args)+b'\0')
        (entry/'stat').write_text(' '.join([str(pid), '(fixture)', 'S']+['0']*18+[str(pid*100)]))
    namespace['Path'] = lambda value: table if str(value) == '/proc' else Path(value)
    loop = next(node for node in tree.body if isinstance(node, ast.While))
    body = next(node for node in loop.body if isinstance(node, ast.Try)).body
    classification = [node for node in body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id in {'ps', 'workers', 'controllers', 'children'}
                              for target in node.targets)]
    assert len(classification) == 4
    exec(compile(ast.Module(body=classification, type_ignores=[]), str(script), 'exec'), namespace)
    assert {p['pid'] for p in namespace['ps']} == {101, 102, 103, 201, 202, 203}
    assert {p['pid'] for p in namespace['controllers']} == {101, 201}
    assert {p['pid'] for p in namespace['workers']} == {102, 202}
    assert {p['pid'] for p in namespace['children']} == {103, 203}
    assert all(p['args'] == rows[p['pid']] and p['start_ticks'] == str(p['pid']*100)
               and p['uid'] == os.getuid() and p['state'] == 'S' for p in namespace['ps'])


class ArchiveFilenameTest(unittest.TestCase):
    def setUp(self):
        # Retain fixtures so failures can be inspected without deleting files.
        self.fixture = Path(tempfile.mkdtemp(prefix="trace-archive-filenames-"))
        self.archive = Archive(self.fixture / "episode", {"qid": "fixture"},
                               assets_root=self.fixture / "blobs",
                               trusted_roots=(self.fixture,))

    def test_snapshot_long_payload_names(self):
        for label in ("a" * 256, "界" * 86):
            for location in ("prompt", "kind"):
                with self.subTest(label_bytes=len(label.encode("utf-8")), location=location):
                    payload = {"prompt": f"Inspect {self.fixture}/{label}"}
                    kind = "planner_payload" if location == "prompt" else label
                    if location == "kind":
                        payload = {"tool_calls": [{"name": label, "args": {"label": label}}]}
                    receipt = self.archive.event(kind, payload)
                    saved = json.loads((self.archive.root / receipt["path"]).read_text())
                    self.assertEqual(saved["payload"], payload)
                    self.assertEqual(saved["kind"], kind)
                    self.assertLess(len(Path(receipt["path"]).name.encode("utf-8")), 200)
                    journal = json.loads(self.archive.journal_path.read_text().splitlines()[-1])
                    if location == "kind":
                        original = f'{receipt["id"]:08d}_{kind}.json'
                        expected = (original.encode("utf-8")[:96].decode("utf-8", "ignore")
                                    + "_" + hashlib.sha256(original.encode("utf-8")).hexdigest()[:16]
                                    + ".json")
                        self.assertEqual(Path(receipt["path"]).name, expected)
                        self.assertEqual(journal["original_name"], original)
                    else:
                        self.assertNotIn("original_name", journal)

    def test_byte_boundary_and_stable_distinct_names(self):
        for name in ("a" * 194 + ".json", "界" * 64 + "ab.json"):
            self.assertEqual(len(name.encode("utf-8")), 199)
            self.assertEqual(_snapshot_name(name), name)
        names = ["a" * 195 + ".json", "a" + "界" * 100 + ".json",
                 "a" + "界" * 100 + "different.json"]
        shortened = [_snapshot_name(name) for name in names]
        self.assertEqual(len(set(shortened)), len(names))
        for name, result in zip(names, shortened):
            self.assertLess(len(result.encode("utf-8")), 200)
            self.assertEqual(_snapshot_name(name), result)
            self.assertIn(hashlib.sha256(name.encode("utf-8")).hexdigest()[:16], result)

    def test_short_event_keeps_existing_schema_and_filename(self):
        receipt = self.archive.event("planner_payload", {"prompt": "hello"})
        self.assertEqual(receipt, {"id": 1, "kind": "planner_payload",
                                   "path": "events/00000001_planner_payload.json"})
        self.assertEqual(json.loads(self.archive.journal_path.read_text()), receipt)
        event = json.loads((self.archive.root / receipt["path"]).read_text())
        self.assertEqual(set(event), {"id", "kind", "time_ns", "payload"})

    def test_explicit_long_asset_path_still_fails(self):
        with self.assertRaises(OSError) as raised:
            self.archive.event("planner_payload", {"asset": self.fixture / ("a" * 256)})
        self.assertEqual(raised.exception.errno, errno.ENAMETOOLONG)

    def test_other_path_errors_still_fail(self):
        for code in (errno.EIO, errno.EACCES):
            with self.subTest(errno=code):
                with patch.object(self.archive, "_trusted", side_effect=OSError(code, "fixture")):
                    with self.assertRaises(OSError) as raised:
                        self.archive.event("planner_payload", {"prompt": f"Inspect {self.fixture}/asset"})
                self.assertEqual(raised.exception.errno, code)
