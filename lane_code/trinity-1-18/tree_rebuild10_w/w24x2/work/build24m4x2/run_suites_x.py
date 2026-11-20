import sys,subprocess,json,time,os,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
L=Path.cwd();D=L/'work/build24m4x2'
results=[]
for name in (sys.argv[1:] or json.loads((D/'suite_names.json').read_text())):
 log=D/(name+'_'+str(time.time_ns())+'.log')
 with log.open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'run_suite.py'),str(D/(name+'.py'))],stdout=f,stderr=-2,env={**os.environ,'B21C_PORTABLE':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'})
 record=dict(name=name,returncode=p.returncode,log=str(log.relative_to(L)));results.append(record)
 prior=json.loads((D/'SUITE_RUNS.json').read_text()) if (D/'SUITE_RUNS.json').exists() else []
 (D/'SUITE_RUNS.json').write_text(json.dumps(prior+[record],indent=2)+'\n')
 print(name,p.returncode,flush=True)
 if p.returncode:print(log.read_text()[-2500:],flush=True)
 if p.returncode<0:print('STOP: killed process, no retry',flush=True);break
