import sys,os,runpy,http.client,ssl,builtins
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
