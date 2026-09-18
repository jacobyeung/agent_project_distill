"""Exercise NFS heartbeat timeouts without providers or shared lease writes."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import uuid
import pytest
import collect


@pytest.mark.parametrize('failures,success,delays', [(1, True, [1]), (2, True, [1, 2]), (3, False, [1, 2])])
def test_heartbeat_timeout_backoff(monkeypatch, failures, success, delays):
    calls=[]; sleeps=[]
    def run(command, **kwargs):
        calls.append(kwargs)
        if len(calls)<=failures:raise subprocess.TimeoutExpired(command,30)
    monkeypatch.setattr(collect.subprocess,'run',run)
    monkeypatch.setattr(collect,'time',SimpleNamespace(sleep=sleeps.append))
    assert collect.heartbeat({'agent_id':'owner','coord_root':'fixture','work_id':'work'}) is success
    assert sleeps==delays and len(calls)==min(3,failures+1)
    assert all(c['timeout']==30 and c['check'] and c['env']['AGENT_ID']=='owner' for c in calls)


def test_heartbeat_ownership_refusal_is_not_retried(monkeypatch):
    calls=[]
    def run(command,**kwargs):
        calls.append(command);raise subprocess.CalledProcessError(1,command)
    monkeypatch.setattr(collect.subprocess,'run',run)
    with pytest.raises(subprocess.CalledProcessError):
        collect.heartbeat({'agent_id':'foreign','coord_root':'fixture','work_id':'work'})
    assert len(calls)==1


@pytest.mark.parametrize('persistent',[False,True])
def test_controller_survives_timeout_and_stops_safely_at_deadline(monkeypatch,persistent):
    root=Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/runtime_control/gt_teacher_r1313/r1315_fixtures')/uuid.uuid4().hex
    root.mkdir(parents=True)
    clock=[100.0];calls=[];ticks=[];stopped=[]
    config={'run_root':str(root),'agent_id':'fixture','coord_root':str(root),'work_id':'fixture'}
    target=SimpleNamespace(state_root=root)
    queue=SimpleNamespace(catalog=SimpleNamespace(episodes=[1]))
    class Controller:
        active={1:True}
        def __init__(self,*a,**k):pass
        def tick(self):
            ticks.append(clock[0])
            if not persistent and len(ticks)==2:self.active={}
            return {'blocked':None,'census':{'total':1,'valid_complete':1 if not self.active else 0}}
        def stop(self):stopped.append(True)
    def run(command,**kwargs):
        calls.append(command)
        if persistent or len(calls)<=3:raise subprocess.TimeoutExpired(command,30)
    def sleep(seconds):clock[0]+=seconds if seconds<3 else (1600 if persistent else 31)
    monkeypatch.setattr(collect,'objects',lambda c:(target,queue,0))
    monkeypatch.setattr(collect,'initialize',lambda *a:None)
    monkeypatch.setattr(collect,'coord_guard',lambda c:{'last_heartbeat':datetime.now(timezone.utc).isoformat()})
    monkeypatch.setattr(collect,'PoolController',Controller)
    monkeypatch.setattr(collect.signal,'signal',lambda *a:None)
    monkeypatch.setattr(collect.subprocess,'run',run)
    monkeypatch.setattr(collect,'time',SimpleNamespace(monotonic=lambda:clock[0],sleep=sleep))
    assert collect._start(SimpleNamespace(workers=64,config=root/'config'),config)==(2 if persistent else 0)
    assert stopped==[True] and ticks
    if persistent:assert json.loads((root/'BLOCKED.json').read_text())['reason']=='coordination_heartbeat_unconfirmed'
    else:assert len(calls)==4 and len(ticks)==2 and not (root/'BLOCKED.json').exists()
