import sys,os,runpy,json,hashlib,base64,concurrent.futures
from pathlib import Path
W=Path(__file__).resolve().parent
m=runpy.run_path(str(W/'kit/b/gc.py'),run_name='fake_gc')
class Reply:
 status=200
 def __init__(self,data):self.data=data
 def read(self):return json.dumps(dict(size=len(self.data),md5Hash=base64.b64encode(hashlib.md5(self.data).digest()).decode(),generation='1')).encode()
class Conn:
 def __init__(self,*a,**k):self.data=bytearray()
 def putrequest(self,method,path):self.name=hashlib.sha256(path.encode()).hexdigest()
 def putheader(self,*a):pass
 def endheaders(self):pass
 def send(self,b):self.data.extend(b)
 def getresponse(self):
  p=Path(os.environ['FAKE_SINK']);p.mkdir(exist_ok=True)
  (p/self.name).write_bytes(self.data)
  return Reply(self.data)
m['upload'].__globals__['http'].client.HTTPSConnection=Conn
m['main'].__globals__['ProcessPoolExecutor']=concurrent.futures.ThreadPoolExecutor
raise SystemExit(m['main'](sys.argv[1:]))
