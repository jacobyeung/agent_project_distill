import sys,subprocess,json,time,os
from pathlib import Path
D=Path(__file__).resolve().parent
names=sys.argv[1:];results=[]
for name in names:
 log=D/(name+'_'+str(time.time_ns())+'.log')
 with log.open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'run_one.py'),str(D/(name+'.py'))],stdout=f,stderr=-2,env={**os.environ,'B21C_PORTABLE':'1'})
 results.append(dict(name=name,returncode=p.returncode,log=str(log)))
 (D/'SUITE_RUNS.json').write_text(json.dumps(results,indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode:print(log.read_text()[-3000:],flush=True)
