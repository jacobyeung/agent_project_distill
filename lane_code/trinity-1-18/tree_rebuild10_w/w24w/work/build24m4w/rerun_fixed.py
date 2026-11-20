from pathlib import Path
import sys,subprocess,json,time,os
L=Path.cwd();D=L/"work/build24m4w"
p=D/"targeted_proofs"
if p.exists():
 a=L/"attic/build24m4w/targeted_proofs";a.parent.mkdir(parents=True,exist_ok=True);p.rename(a)
runs=[]
for n in ("tree_tests","guard_q_new","guard_q_legacy","guard_n_new","guard_n_legacy"):
 log=D/(n+"_fixed_"+str(time.time_ns())+".log")
 with log.open("w") as f:p=subprocess.run([sys.executable,"-I","-s","-B",str(D/"run_suite.py"),str(D/(n+".py"))],stdout=f,stderr=-2,env={**os.environ,"B21C_PORTABLE":"1"})
 runs.append(dict(name=n,log=str(log.relative_to(L)),returncode=p.returncode));(D/"FIXED_RUNS.json").write_text(json.dumps(runs,indent=2)+"\n")
 print(n,p.returncode,flush=True)
 if p.returncode:print(log.read_text()[-4000:])
 if p.returncode<0:break
