import sys,subprocess,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,seal
k=Path(__file__).resolve().parents[1];seal(k)
if load(k/'k/a.json')['GO'] is not True:raise SystemExit(0)
if len(sys.argv)!=3:raise ValueError('E80')
raise SystemExit(subprocess.run([sys.executable,'-s','-B','-m','torch.distributed.run','--standalone','--nnodes=1','--nproc_per_node=4','--no-python','/bin/bash',str(k/'b/e.sh'),sys.executable,*sys.argv[1:]],check=False,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}).returncode)
