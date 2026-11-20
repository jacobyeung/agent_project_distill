from pathlib import Path
import subprocess,sys,json,time,os
L=Path.cwd();D=L/"work/build24m4w";names=sys.argv[1:];results=[]
for name in names:
 for rel in {"sample_tests":["sample/rcj_l"],"contract_tests":["contract/rcj_contract"],"recorder_tests":["recorder"],"publication_integration":["real/pool/o/173724"]}.get(name,[]):
  p=D/rel
  if p.exists():
   saved=L/"attic/build24m4w/extra"/(rel+"_"+str(time.time_ns()));saved.parent.mkdir(parents=True,exist_ok=True);p.rename(saved)
 log=D/(name+"_extra_"+str(time.time_ns())+".log")
 with log.open("w") as f:p=subprocess.run([sys.executable,"-I","-s","-B",str(D/"run_suite.py"),str(D/(name+".py"))],stdout=f,stderr=-2,env={**os.environ,"B21C_PORTABLE":"1"})
 results.append(dict(name=name,returncode=p.returncode,log=str(log.relative_to(L))))
 existing=json.loads((D/"EXTRA_RUNS.json").read_text()) if (D/"EXTRA_RUNS.json").exists() else []
 (D/"EXTRA_RUNS.json").write_text(json.dumps(existing+[results[-1]],indent=2)+"\n")
 print(name,p.returncode,flush=True)
 if p.returncode:print(log.read_text()[-5000:])
 if p.returncode<0:break
