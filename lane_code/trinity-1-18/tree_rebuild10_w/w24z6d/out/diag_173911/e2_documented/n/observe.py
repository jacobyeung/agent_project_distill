import sys,os,runpy,http.client,time,types,subprocess
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
