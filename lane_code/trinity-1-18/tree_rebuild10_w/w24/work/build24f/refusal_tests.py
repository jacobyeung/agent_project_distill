from pathlib import Path
import sys,subprocess,json,os
L=Path(__file__).resolve().parents[2];D=L/"work/build24f";sys.path.insert(0,str(L/"work/build24"));import joblib as J
records=[]
for name in ("q","n","n_go"):
 k=L/"out/kit_n_go" if name=="n_go" else L/"work/build24/kits"/name
 before={str(p.relative_to(k)):J.sha(p) for p in k.rglob("*") if p.is_file()}
 for script,arg,code in (("b/f.sh","proof","E06"),("b/f.sh","/tmp","E06"),("b/f.sh","/tmp/../scratch/rejected","E06"),("job.sh","absent_request.json","E87")):
  r=subprocess.run(["bash",script,arg],cwd=k,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  assert r.returncode and code in r.stdout,(script,r.stdout)
  assert before=={str(p.relative_to(k)):J.sha(p) for p in k.rglob("*") if p.is_file()}
  records.append(dict(kit=name,seal=J.seal(k),script=script,arg=arg,refusal=code,unchanged=True))
J.write(D/"FINAL_REFUSALS.json",dict(status="PASS",tests=len(records),records=records));print("PASS",len(records))
