import sys,os,runpy,json,hashlib,base64,concurrent.futures
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z4/work/enospc4')
m=runpy.run_path(str(W/'kit/b/gc.py'),run_name='fake_gc')
class Reply:
 status=200
 def __init__(self,data):self.data=data
 def read(self):return json.dumps(dict(size=len(self.data),md5Hash=base64.b64encode(hashlib.md5(self.data).digest()).decode(),generation='1')).encode()
class Conn:
 def __init__(self,*a,**k):self.data=bytearray()
 def putrequest(self,method,path):self.path=path;self.name=hashlib.sha256(path.encode()).hexdigest()
 def putheader(self,*a):pass
 def endheaders(self):pass
 def send(self,b):self.data.extend(b)
 def getresponse(self):
  p=Path(os.environ['FAKE_SINK']);p.mkdir(exist_ok=True)
  if self.path.endswith('/2?') and not (p/'failed_once').exists():
   (p/'failed_once').write_text('1')
   raise OSError('E104')
  with (p/'requests.jsonl').open('a') as f:f.write(json.dumps(dict(name=self.name))+'\n')
  (p/self.name).write_bytes(self.data)
  return Reply(self.data)
m['upload'].__globals__['http'].client.HTTPSConnection=Conn
m['main'].__globals__['ProcessPoolExecutor']=concurrent.futures.ThreadPoolExecutor
m['upload'].__globals__['time'].sleep=lambda _:None
raise SystemExit(m['main'](sys.argv[1:]))
