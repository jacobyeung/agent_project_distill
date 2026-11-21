# fix14 copy of the kit's b/t.py; the only difference: e2.sh in place of b/e.sh.
import sys,subprocess,os
from pathlib import Path
k=Path(os.environ['Q_KIT']).resolve()
sys.path.insert(0,str(k/'b'))
from z import load,seal
seal(k)
if load(k/'k/a.json')['GO'] is not True:raise SystemExit(0)
if len(sys.argv)!=3:raise ValueError('E80')
raise SystemExit(subprocess.run([sys.executable,'-s','-B','-m','torch.distributed.run','--standalone','--nnodes=1','--nproc_per_node=4','--no-python','/bin/bash','/tmp/a15_dbg_174134/tr2/e2.sh',sys.executable,*sys.argv[1:]],check=False,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}).returncode)
