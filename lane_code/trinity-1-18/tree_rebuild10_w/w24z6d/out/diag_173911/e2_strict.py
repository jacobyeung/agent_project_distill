"""Run sealed E2 bytes with a strict no-network sink and a scaled clock."""
from pathlib import Path
import importlib.util,json,os,sys,shutil,subprocess,tarfile,hashlib,types,time,resource
J=Path.cwd();D=J/"out/e2";HERE=J/"out/diag_173911"
mode=sys.argv[1];W=HERE/("e2_"+mode);W.mkdir()
N=W/"n";X=W/"x";N.mkdir();X.mkdir()
for name in ("tmp","probe","logs","obs","bin"):(N/name).mkdir()
job="24045"
os.environ.update(E2_N=str(N),E2_PY=sys.executable,SLURM_JOB_ID=job,TMPDIR=str(N/"tmp"),STRICT_SINK=str(N/"sink"),
                  OMP_NUM_THREADS="4",OPENBLAS_NUM_THREADS="4",MKL_NUM_THREADS="4",NUMEXPR_NUM_THREADS="4")
os.environ["REQUIRE_RANGE"]="1" if mode=="explicit_range" else "0"
spec=importlib.util.spec_from_file_location("e2_driver",D/"e2.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original=m.load
def load(p):
 v=original(p)
 if Path(p).name=="p.json":v["n_root"]=str(X)
 return v
m.load=load
(X/"n_s").mkdir(mode=0o700)
names=load(J/"out/kit_n/k/y.json")["objects"]
values={v+".j"+job+f".part{i:02d}-of-04":"https://local.invalid/"+v+".j"+job+f".part{i:02d}-of-04" for v in names.values() for i in range(4)}
p=X/"n_s"/("sess_"+job+".json");p.write_text(json.dumps(values));p.chmod(0o600)
m.stage(D,N,X,job)
if mode.startswith("patched"):
 spec2=importlib.util.spec_from_file_location("e2_proposed",HERE/"proposed/e2.py");m=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(m)
shutil.copyfile(N/"observe.py",N/"observe_actual.py")
if mode.startswith("patched"):
 shutil.copyfile(HERE/"proposed/observe.py",N/"observe_actual.py")
# This is an unsealed test adapter; the kit sources stay byte-identical.
adapter=r"""import sys,os,runpy,http.client,time,types,subprocess
from pathlib import Path
N=Path(os.environ["E2_N"]);K=N/"k";X=N.parent/"x"
sys.path.insert(0,str(Path.cwd()/"out/diag_173911"))
from strict_sink import Connection
http.client.HTTPSConnection=Connection
sys.path.insert(0,str(K/"b"))
import z
oldload=z.load
def load(p):
 v=oldload(p)
 if Path(p).name=="p.json":v["n_root"]=str(X)
 return v
z.load=load
original_run=subprocess.run
def capture(argv,*a,**kw):
 if isinstance(argv,list) and str(K/"b/gc.py") in argv:
  with (N/"logs"/("gc_"+str(os.getpid())+".log")).open("a") as f:
   kw.update(stdout=f,stderr=f)
   return original_run(argv,*a,**kw)
 return original_run(argv,*a,**kw)
subprocess.run=capture
original=runpy.run_path
def run(path,*a,**kw):
 if Path(path).name=="pc.py":
  d=original(path,run_name="case_pc");old=d["read"]
  def read(p):
   v=old(p)
   if Path(p).name=="p.json":v["n_root"]=str(X)
   return v
  g=d["main"].__globals__;g["read"]=read
  g["time"]=types.SimpleNamespace(time=time.time,monotonic=lambda:time.monotonic()/.02,sleep=lambda s:time.sleep(s*.02))
  d["main"]();return d
 return original(path,*a,**kw)
runpy.run_path=run
run(str(N/"observe_actual.py"),run_name="__main__")
"""
(N/"observe.py").write_text(adapter)
# E2 poll windows are scaled separately; preserve enough time for child startup.
m.time=types.SimpleNamespace(time=time.time,monotonic=lambda:time.monotonic()/.05,sleep=lambda s:time.sleep(s*.05))
rc=m.run(N,X,job)
report=m.load(N/"E2.json")
m.finish(N,X,job,rc)
requests=[json.loads(s) for s in (N/"sink/requests.jsonl").read_text().splitlines()] if (N/"sink/requests.jsonl").exists() else []
from collections import Counter
result=dict(mode=mode,job_status=report["status"],checks=report["checks"],objects=len(report["objects"]),
            request_statuses=dict(Counter(str(r["status"]) for r in requests)),
            reasons=dict(Counter(r["reason"] for r in requests)),python=sys.version,
            adapters=["in-memory n_root", "no-socket HTTPS protocol model", "copier clock .02", "E2 clock .05", "retain gc child stderr"])
(W/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,sort_keys=True),flush=True)
raise SystemExit(rc)
