import os,sys,subprocess,json,time
from pathlib import Path
D=Path(__file__).resolve().parent;rows=[]
for name in sys.argv[1:]:
 log=D/(name+'_'+str(time.time_ns())+'.log')
 with log.open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',*([] if name=='audit' else [str(D/'run_suite.py')]),str(D/(name+'.py'))],stdout=f,stderr=-2,env={**os.environ,'B21C_PORTABLE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'})
 rows.append(dict(name=name,returncode=p.returncode,log=str(log)))
 (D/'SUITES.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:print(log.read_text()[-2200:],flush=True)
