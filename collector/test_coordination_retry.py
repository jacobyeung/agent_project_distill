"""Exercise coordination failures without providers or shared lease writes."""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import uuid
import pytest
import collect


@pytest.fixture
def heartbeat_config():
    root = Path(os.environ['REMEDIATION_FIXTURE_ROOT']) / uuid.uuid4().hex
    root.mkdir(parents=True)
    return {'run_root': str(root), 'agent_id': 'owner', 'coord_root': str(root), 'work_id': 'work'}


@pytest.mark.parametrize('kind', ['timeout', 'exit', 'oserror'])
@pytest.mark.parametrize('failures', [1, 2, 3])
def test_heartbeat_failure_backoff_and_durable_exhaustion(monkeypatch, heartbeat_config, kind, failures):
    calls=[]; sleeps=[]
    def run(command, **kwargs):
        calls.append(kwargs)
        if len(calls) <= failures:
            if kind == 'timeout': raise subprocess.TimeoutExpired(command, 30, stderr='lock timeout')
            if kind == 'exit': raise subprocess.CalledProcessError(1, command, stderr='lock contention')
            raise OSError('NFS unavailable')
    monkeypatch.setattr(collect, 'coord_guard', lambda c: {})
    monkeypatch.setattr(collect.subprocess, 'run', run)
    monkeypatch.setattr(collect, 'time', SimpleNamespace(sleep=sleeps.append))
    assert collect.heartbeat(heartbeat_config) is (failures < 3)
    assert sleeps == ([1] if failures == 1 else [1, 2])
    assert len(calls) == min(3, failures+1)
    assert all(c['timeout'] == 30 and c['check'] and c['env']['AGENT_ID'] == 'owner' for c in calls)
    pool = Path(heartbeat_config['run_root']) / 'pool_b16384'
    receipts = list((pool / 'coordination_failures').glob('*.json'))
    assert len(receipts) == failures
    assert all(json.loads(p.read_text())['error']['message'] for p in receipts)
    if failures == 3:
        blocked = json.loads((pool / 'BLOCKED.json').read_text())
        assert blocked['reason'] == 'coordination_heartbeat_exhausted'
        assert set(blocked['failure_receipts']) == {str(p) for p in receipts}
    else: assert not (pool / 'BLOCKED.json').exists()


@pytest.mark.parametrize('change_after_failure', [False, True])
def test_heartbeat_ownership_refusal_is_not_retried(monkeypatch, heartbeat_config, change_after_failure):
    calls = []
    lease = Path(heartbeat_config['coord_root']) / 'LEASES/work.lock/lease.json'
    lease.parent.mkdir(parents=True)
    def publish(owner):
        lease.write_text(json.dumps({'work_id': 'work', 'status': 'running', 'agent_id': owner,
                                    'last_heartbeat': datetime.now(timezone.utc).isoformat()}))
    heartbeat_config['mode'] = 'offline_fixture'
    # Retain the real owner/status/age check; scope this synthetic coordination root.
    monkeypatch.setattr(collect, 'DATA_ROOT', Path(heartbeat_config['coord_root']).parents[1])
    original_guard = collect.coord_guard
    def guard(config):
        scoped = dict(config, mode='production')
        return original_guard(scoped)
    monkeypatch.setattr(collect, 'COORD_ROOT', Path(heartbeat_config['coord_root']))
    monkeypatch.setattr(collect, 'coord_guard', guard)
    publish('owner' if change_after_failure else 'foreign')
    def run(command, **kwargs):
        calls.append(command)
        publish('foreign')
        raise subprocess.CalledProcessError(1, command, stderr='heartbeat requires the lease owner')
    monkeypatch.setattr(collect.subprocess, 'run', run)
    monkeypatch.setattr(collect, 'time', SimpleNamespace(sleep=lambda _: None))
    with pytest.raises(RuntimeError, match='foreign'):
        collect.heartbeat(heartbeat_config)
    assert len(calls) == int(change_after_failure)
    blocked = Path(heartbeat_config['run_root']) / 'pool_b16384/BLOCKED.json'
    assert json.loads(blocked.read_text())['reason'] == 'coordination_lease_rejected'


@pytest.mark.parametrize('persistent', [False, True])
def test_controller_retries_real_heartbeat_then_stops_on_exhaustion(monkeypatch, heartbeat_config, persistent):
    from test_tolerant_pool import make_queue
    root = Path(heartbeat_config['run_root'])
    target, queue = make_queue(root / 'pool_b16384', cap=64, count=1)
    clock=[100.0]; calls=[]; ticks=[]; stopped=[]
    class Controller:
        active={1: True}
        def __init__(self, *a, **k): pass
        def tick(self):
            ticks.append(clock[0]); self.active={}
            return {'blocked': None, 'census': {'total': 1, 'valid_complete': 1}}
        def stop(self): stopped.append(True)
    def run(command, **kwargs):
        calls.append(command)
        if persistent or len(calls) <= 2: raise subprocess.TimeoutExpired(command, 30)
    monkeypatch.setattr(collect, 'objects', lambda c: (target, queue, 0))
    monkeypatch.setattr(collect, 'coord_guard', lambda c: {'last_heartbeat': datetime.now(timezone.utc).isoformat()})
    monkeypatch.setattr(collect, 'PoolController', Controller)
    monkeypatch.setattr(collect.signal, 'signal', lambda *a: None)
    monkeypatch.setattr(collect.subprocess, 'run', run)
    monkeypatch.setattr(collect, 'time', SimpleNamespace(monotonic=lambda: clock[0], sleep=lambda n: clock.__setitem__(0, clock[0]+n)))
    assert collect._start(SimpleNamespace(workers=64, config=root/'config'), heartbeat_config) == (2 if persistent else 0)
    assert stopped == [True] and len(calls) == 3
    assert len(ticks) == (0 if persistent else 1)
    assert (target.state_root/'BLOCKED.json').exists() is persistent
