"""Bound the entire worker process and reserve the inherited return interval."""
import os
import signal
import subprocess
import time
from .paths import V1, module
from .io import dump


def run(argv, cwd, receipt, *, deadline_utc, limit=21600, reserve=600, env=None):
    if limit<=0 or limit>21600 or reserve<0:
        raise ValueError('invalid worker time budget')
    B = module('_native_v1_budget',V1/'budget.py')
    end = min(B.timestamp(deadline_utc), time.time()+limit+reserve)
    kill_at = end-reserve
    if kill_at<=time.time():
        raise TimeoutError('return reserve already started')
    from datetime import datetime,timezone
    environment = dict(os.environ, **(env or {}))
    environment['OFFNATIVE_DEADLINE'] = datetime.fromtimestamp(end,timezone.utc).isoformat()
    start = time.monotonic()
    result = {'subprocess_kill':kill_at,'return_seconds':reserve,'timed_out':False}
    # Only this newly created child session can be stopped by this watchdog.
    with open(str(receipt)+'.log','xb') as log:
        child = subprocess.Popen(argv,cwd=cwd,env=environment,stdout=log,stderr=log,start_new_session=True)
        try:
            result['returncode']=child.wait(timeout=max(.001,kill_at-time.time()))
        except subprocess.TimeoutExpired:
            result['timed_out']=True
            os.killpg(child.pid,signal.SIGKILL)
            result['returncode']=child.wait()
        finally:
            result['seconds']=time.monotonic()-start
            dump(receipt,result)
    return result
