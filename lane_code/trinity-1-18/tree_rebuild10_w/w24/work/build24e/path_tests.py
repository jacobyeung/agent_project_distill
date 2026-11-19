from pathlib import Path
import sys,os,shutil,subprocess,json
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";sys.path.insert(0,str(L/"work/build24"));import joblib as J
O=D/"path_tests";O.mkdir(exist_ok=True);records=[]
def files(k):return {str(p.relative_to(k)):J.sha(p) if p.is_file() else "DIR" for p in k.rglob("*")}
for name in ("q","n","n_go"):
 source=L/"out/kit_n_go" if name=="n_go" else L/"work/build24/kits"/name
 old=L/"attic/build24e"/source.relative_to(L)
 for version,src in (("before",old),("after",source)):
  k=O/(name+"_"+version);shutil.copytree(src,k);before=files(k)
  r=subprocess.run(["bash","b/f.sh","proof"],cwd=k,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  after=files(k);assert r.returncode!=0
  if version=="before":assert "proof.h/tmp" in after and before!=after
  else:assert before==after and "E06" in r.stdout
  records.append(dict(kit=name,version=version,test="f.sh relative output",returncode=r.returncode,unchanged=before==after,refusal=r.stdout[-700:]))
 # Probe request resolution with stub helpers; no model or staging involved.
 for version,src in (("before",old),("after",source)):
  k=O/(name+"_job_"+version);shutil.copytree(src,k)
  (k/"b/v.py").write_text("pass\n")
  (k/"b/x.py").write_text("import pathlib,sys\np=pathlib.Path(sys.argv[2]);print(\x27E88:\x27+str(p)+\x27:\x27+str(p.is_file()));raise SystemExit(1)\n")
  (k/"b/l.py").write_text("import sys\nsys.stdout.write(sys.stdin.read())\n")
  (k/"request.json").write_text("{}\n");before=files(k)
  r=subprocess.run(["bash","job.sh","request.json"],cwd=k,env={**os.environ,"SLURM_TMPDIR":str(O),"SLURM_JOB_ID":name+version},text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  assert before==files(k) and r.returncode
  if version=="before":assert "E88:request.json:False" in r.stdout
  else:assert "E88:"+str(k/"request.json")+":True" in r.stdout
  records.append(dict(kit=name,version=version,test="job.sh relative request",unchanged=True,refusal=r.stdout.strip()))
J.write(D/"PATH_TESTS.json",dict(status="PASS",tests=len(records),records=records));print(len(records),"PASS")
