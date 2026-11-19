"""Exercise the real shell trap and rank poll, then probe the gloo boundary."""
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';P=L/'work/build7/proofs/stop'
P.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(T))
from student_pilot.stop_control import requested
for name in ('host/o','node/o'):(P/name).mkdir(parents=True,exist_ok=True)
text=(T/'launch_s1/b/r.sh').read_text()
trap=text[text.index('on_stop() {'):text.index('trap on_stop USR1')+len('trap on_stop USR1')]
script=P/'batch.sh'
script.write_text('#!/bin/bash\nset -euo pipefail\nHX="$1/host"\nNX="$1/node"\nstop_file="$HX/o/local.stop"\nchild=""\nadmission_child=""\nX=""\n'+trap+'\nprintf ready > "$1/ready"\nsleep 3 &\nwait $! || true\n')
child=subprocess.Popen(['bash',str(script),str(P)])
deadline=time.monotonic()+10
while not (P/'ready').exists():
 if child.poll() is not None or time.monotonic()>deadline:raise RuntimeError('shell did not become ready')
 time.sleep(.02)
os.kill(child.pid,signal.SIGUSR1);rc=child.wait(timeout=10)
os.environ['K3']=str(P/'node/o/local.stop')
assert requested(False,{},1)
assert requested(False,{'stop_after_step':2},2)
paths={str(p.relative_to(L)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (P/'host/o/local.stop',P/'node/o/local.stop')}
result=dict(shell_returncode=rc,trap_source='work/tree_r1/launch_s1/b/r.sh',stop_files=paths,
            native_rank_poll=True,full_wrapper_chain=False,end_slot=None)
try:
 import datetime
 import torch.distributed as dist
 store=dist.FileStore(str(L/'work/tmp/b7_gloo_probe'),1)
 dist.init_process_group('gloo',store=store,rank=0,world_size=1,timeout=datetime.timedelta(seconds=15))
 result['gloo_boundary']='available'
 dist.destroy_process_group()
except Exception as e:
 result['gloo_boundary']='blocked';result['gloo_error']=type(e).__name__+': '+str(e)
(P/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
