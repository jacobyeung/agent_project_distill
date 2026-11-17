import os,sys,subprocess,time,json
from pathlib import Path
W=Path(__file__).resolve().parents[1];O=W/'out'
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',XDG_CACHE_HOME=str(W/'work/cache'),TMPDIR=str(W/'work/tmp'))
(W/'work/tmp').mkdir(exist_ok=True)
cmd=sys.argv[2:];name=sys.argv[1];start=time.time()
with (O/(name+'.log')).open('w') as f:
 p=subprocess.run(cmd,cwd=W,env=env,stdout=f,stderr=subprocess.STDOUT)
with (O/'TESTS.txt').open('a') as f:f.write(json.dumps(dict(command=cmd,exit=p.returncode,seconds=round(time.time()-start,3),log=name+'.log'))+'\n')
print(name,p.returncode,(O/(name+'.log')).read_text()[-1800:])

raise SystemExit(p.returncode)
