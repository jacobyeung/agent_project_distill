# Copy of the kit's b/t.py. Differences: the kit is $Q_KIT (this file lives outside it); the rank shell is
# e2.sh beside this file; --standalone (c10d on localhost:0, a free port) is spelled out as the same
# c10d rendezvous on localhost:$A15_PORT, a fixed port below the ephemeral range, so the rehearsal never
# shares the job's port.
import sys,subprocess,os,json
from pathlib import Path
k=Path(os.environ['Q_KIT']).resolve();sys.path.insert(0,str(k/'b'))
from z import load,seal
seal(k)
if load(k/'k/a.json')['GO'] is not True:raise SystemExit(0)
if len(sys.argv)!=3:raise ValueError('E80')
here=Path(__file__).resolve().parent
cmd=[sys.executable,'-s','-B','-m','torch.distributed.run','--rdzv-backend=c10d','--rdzv-endpoint=localhost:'+os.environ['A15_PORT'],'--rdzv-id=a15rh'+os.environ.get('SLURM_JOB_ID','0'),'--nnodes=1','--nproc_per_node=4','--no-python','/bin/bash',str(here/'e2.sh'),sys.executable,*sys.argv[1:]]
print(json.dumps(dict(a15_launch=cmd)),flush=True)
raise SystemExit(subprocess.run(cmd,check=False,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}).returncode)
