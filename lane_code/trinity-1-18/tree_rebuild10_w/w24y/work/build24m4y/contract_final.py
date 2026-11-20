from pathlib import Path
import sys,subprocess,json,time,os
L=Path.cwd();D=L/"work/build24m4y";p=D/"contract/rcj_contract"
if p.exists():
 a=L/"attic/build24m4y/contract_missing_rdiff";a.parent.mkdir(parents=True,exist_ok=True);p.rename(a)
log=D/"contract_final.log"
with log.open("w") as stream:r=subprocess.run([sys.executable,"-I","-s","-B",str(D/"run_suite.py"),str(D/"contract_tests.py")],stdout=stream,stderr=-2,env={**os.environ,"B21C_PORTABLE":"1"})
(D/"CONTRACT_FINAL_RUN.json").write_text(json.dumps(dict(name="contract_tests",returncode=r.returncode,log=str(log.relative_to(L))),indent=2)+"\n")
print(r.returncode,log.read_text()[-2000:]);raise SystemExit(r.returncode)
