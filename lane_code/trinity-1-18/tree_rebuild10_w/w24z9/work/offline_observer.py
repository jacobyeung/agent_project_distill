"""Test-only transport and clock adapter; the real HTTPS constructor stays intact."""
import os,sys,runpy,http.client,time,types,socket
from pathlib import Path
N=Path(os.environ["E3_N"]);K=N/"k"
sys.path.insert(0,os.environ["E3_TEST_WORK"])
from strict_sink import Connection
C=http.client.HTTPSConnection
original_init=C.__init__
def putrequest(self,method,path,*a,**kw):
 self.headers={};self.data=bytearray();self.method=method;self.path=path
C.putrequest=putrequest
for name in ("putheader","endheaders","send","close","getresponse","respond"):
 setattr(C,name,getattr(Connection,name))
assert C.__init__ is original_init and http.client.HTTPSConnection is C

def audit(event,args):
 if event in ("socket.connect","socket.getaddrinfo","socket.bind"):raise AssertionError("NETWORK_FORBIDDEN")
sys.addaudithook(audit)
if "--writer" in sys.argv:os.environ["STRICT_SESSIONS"]=sys.argv[sys.argv.index("--writer")+3]
sys.path.insert(0,str(K/"b"))
# Only the legacy local-path test needs a path adapter. The Trinity test uses E08 unchanged.
if os.environ.get("E3_TEST_MAP"):
 import z
 oldload=z.load
 def load(p):
  v=oldload(p)
  if Path(p).name=="p.json":v["n_root"]=os.environ["E3_TEST_MAP"]
  return v
 z.load=load
original=runpy.run_path
def run(path,*a,**kw):
 if Path(path).name=="pc.py":
  d=original(path,run_name="case_pc");g=d["main"].__globals__;old=g["read"]
  def read(p):
   v=old(p)
   if Path(p).name=="p.json" and os.environ.get("E3_TEST_MAP"):v["n_root"]=os.environ["E3_TEST_MAP"]
   return v
  g["read"]=read;g["deadline"]=lambda:time.time()+5;g["ARCHIVE_SECONDS"]=1
  g["time"]=types.SimpleNamespace(time=time.time,monotonic=lambda:time.monotonic()/.003,sleep=lambda s:time.sleep(s*.003))
  if "--writer" in sys.argv:raise SystemExit(d["writer_main"](sys.argv[sys.argv.index("--writer")+1:]))
  elif "--seconds" in sys.argv:print(6)
  else:d["main"]()
  return d
 return original(path,*a,**kw)
runpy.run_path=run
run(str(N/"observe_actual.py"),run_name="__main__")
