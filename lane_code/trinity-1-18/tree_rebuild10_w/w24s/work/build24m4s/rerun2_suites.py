import sys,subprocess,json,time,os
from pathlib import Path
D=Path(__file__).resolve().parent
results=[]
for name in sys.argv[1:]:
 log=D/(name+'_'+str(time.time_ns())+'.log')
 with log.open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'run_suite.py'),str(D/(name+'.py'))],stdout=f,stderr=-2,env={**os.environ,'B21C_PORTABLE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'})
 results.append(dict(name=name,returncode=p.returncode,log=str(log.relative_to(D.parents[1]))))
 (D/'RERUN2_RUNS.json').write_text(json.dumps(results,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode:print(log.read_text()[-3500:],flush=True)
