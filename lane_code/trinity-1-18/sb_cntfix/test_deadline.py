"""Exercise an in-flight CPU deadline without signals to any other process."""
import importlib,os,sys,time
from pathlib import Path
sys.path.insert(0,'kit/files');import count_guard as G
sys.path.insert(0,'/scratch/jjyeung/orch_n30/b05_owngrd/code')
import torch
from owngrd import teacher as T
import run_count_teacher as runner
R=Path.cwd();M=R/'out/MANIFEST_R0DEV.json';out=R/'out/deadline_inside'
# The fake run_capture sleeps inside this process; the runner's own alarm must interrupt it.
def slow_capture(*args,**kwargs):time.sleep(3);raise AssertionError('deadline was not enforced inside capture')
T.run_capture=slow_capture
sys.argv=['run_count_teacher.py','--manifest',str(M),'--manifest-sha256',G.sha(M),'--out',str(out),'--stub','--hours',str(.1/3600),'--deadline-unix',str(time.time()+30)]
start=time.time();rc=runner.main();elapsed=time.time()-start
state=G.read(out/'RUNTIME.json')
assert rc==3 and state['status']=='time_cap' and elapsed<2,(rc,state,elapsed)
G.write(R/'out/DEADLINE_TEST.json',dict(returncode=rc,elapsed_seconds=elapsed,budget_seconds=.1,status=state['status'],inputs_sha256={str(M):G.sha(M),str(__file__):G.sha(__file__),**G.pins()}))
print('in-flight deadline check passed',elapsed)
