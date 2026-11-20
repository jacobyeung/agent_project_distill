"""Fault injection: real gc.py, proposed observer, four parts, no sockets."""
from pathlib import Path
import json,os,sys,shutil,subprocess
H=Path(__file__).resolve().parent;J=Path.cwd();results=[]
for mode in ("tls","forbidden","incomplete","json","receipt_disk"):
 n=H/("failure_"+mode);(n/"k/b").mkdir(parents=True);(n/"obs").mkdir();(n/"logs").mkdir();(n/"sink").mkdir()
 shutil.copyfile(J/"out/kit_n/b/gc.py",n/"k/b/gc.py")
 shutil.copyfile(H/"proposed/observe.py",n/"observe.py")
 names=["object.part%02d-of-04"%i for i in range(4)]
 (n/"sessions.json").write_text(json.dumps({name:"https://local.invalid/"+name for name in names}))
 (n/"payload").write_bytes(b"q"*64)
 (n/"adapter.py").write_text(r"""import sys,os,runpy,http.client,ssl,builtins
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"out/diag_173911"))
from strict_sink import Connection as Base, Reply
mode=os.environ["FAULT"]
class Connection(Base):
 def endheaders(self):
  if mode=="tls":raise ssl.SSLCertVerificationError("https://secret.invalid/?upload_id=CAPABILITY_SENTINEL Authorization: Bearer TOKEN_SENTINEL")
 def getresponse(self):
  if mode=="forbidden":return Reply(403,b"https://secret.invalid/?upload_id=CAPABILITY_SENTINEL Authorization: Bearer TOKEN_SENTINEL")
  if mode=="incomplete":return Reply(308,headers={"Range":"bytes=0-15"})
  if mode=="json":return Reply(200,b"CAPABILITY_SENTINEL")
  return super().getresponse()
http.client.HTTPSConnection=Connection
if mode=="receipt_disk":
 original=builtins.open
 def opened(path,*args,**kwargs):
  if str(path).endswith(".receipts.jsonl") and args and args[0]=="a":raise OSError(28,"CAPABILITY_SENTINEL")
  return original(path,*args,**kwargs)
 builtins.open=opened
runpy.run_path(str(Path(os.environ["E2_N"])/"observe.py"),run_name="__main__")
""")
 env={**os.environ,"E2_N":str(n),"STRICT_SINK":str(n/"sink"),"REQUIRE_RANGE":"0","FAULT":mode,"TMPDIR":str(n)}
 p=subprocess.run([sys.executable,"-I","-s","-B",str(n/"adapter.py"),str(n/"k/b/gc.py"),"split",str(n/"sessions.json"),"object",str(n/"payload"),"4","4"],capture_output=True,text=True,env=env,timeout=30)
 (n/"output.log").write_text(p.stdout+p.stderr)
 raw=(n/"logs/upload.jsonl").read_text();receipt=n/"sessions.json.receipts.jsonl"
 assert "CAPABILITY_SENTINEL" not in raw+p.stdout+p.stderr and "TOKEN_SENTINEL" not in raw+p.stdout+p.stderr
 assert "https://" not in raw+p.stdout+p.stderr
 assert p.returncode==1 and not receipt.exists(), (mode,p.returncode)
 events=[json.loads(s) for s in raw.splitlines()]
 assert any(e["event"] in ("gc_stderr","child_error") for e in events)
 results.append(dict(mode=mode,returncode=p.returncode,receipts=0,observations=len(list((n/"obs").glob("*.json"))),
                     http_statuses=[e["status"] for e in events if e["event"]=="http_status"],
                     error_classes=sorted({x for e in events for x in e.get("errors",[])}|{e["error"] for e in events if "error" in e}),secret_leak=False))
(H/"failure_tests.json").write_text(json.dumps(results,indent=2)+"\n")
print(json.dumps(results,sort_keys=True))
