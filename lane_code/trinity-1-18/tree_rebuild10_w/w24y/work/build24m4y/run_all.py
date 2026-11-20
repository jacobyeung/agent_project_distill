from pathlib import Path
import subprocess,json,sys,time,os
L=Path.cwd();D=L/"work/build24m4y";V=L.parent/"w24v/work/build24m4v"
names=["replay","tree_tests","real_tests","cards"]+[r["name"] for r in json.loads((V/"FINAL_SUITE_RUNS.json").read_text())]
names+= ["new_tests","publication_integration","bind_tests"]
names=list(dict.fromkeys(names));(D/"PLANNED_SUITES.json").write_text(json.dumps(names,indent=2)+"\n")
results=[]
for name in names:
 log=D/(name+"_"+str(time.time_ns())+".log")
 with log.open("w") as f:
  p=subprocess.run([sys.executable,"-I","-s","-B",str(D/"run_suite.py"),str(D/(name+".py"))],stdout=f,stderr=-2,env={**os.environ,"B21C_PORTABLE":"1"})
 record=dict(name=name,returncode=p.returncode,log=str(log.relative_to(L)));results.append(record)
 (D/"RUNS.json").write_text(json.dumps(results,indent=2)+"\n")
 print(name,p.returncode,flush=True)
 if p.returncode:print(log.read_text()[-4500:],flush=True)
 if p.returncode<0:
  print("STOP: child killed; no retry",flush=True);break
