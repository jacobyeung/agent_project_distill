import sys,os,runpy,http.client,json,hashlib,base64,time,types
from pathlib import Path
N=Path(os.environ['E2_N']);K=N/'k';X=N.parent/'x'
sys.path.insert(0,str(K/'b'))
import z
oldload=z.load
def load(p):
 v=oldload(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
z.load=load
class Reply:
 status=200
 def __init__(self,data,name):self.data=data;self.name=name
 def read(self):return json.dumps(dict(size=str(len(self.data)),md5Hash=base64.b64encode(hashlib.md5(self.data).digest()).decode(),crc32c='fixture',name=self.name,generation='1')).encode()
class Connection:
 def __init__(self,*a,**kw):self.data=bytearray()
 def putrequest(self,method,path):self.name=path.split('?')[0].lstrip('/')
 def putheader(self,*a):pass
 def endheaders(self):pass
 def send(self,data):self.data.extend(data)
 def getresponse(self):
  p=N/'sink';p.mkdir(exist_ok=True)
  (p/hashlib.sha256(self.name.encode()).hexdigest()).write_bytes(self.data)
  return Reply(self.data,self.name)
http.client.HTTPSConnection=Connection
original=runpy.run_path
def run(path,*a,**kw):
 if Path(path).name=='pc.py':
  d=original(path,run_name='case_pc');old=d['read']
  def read(p):
   v=old(p)
   if Path(p).name=='p.json':v['n_root']=str(X)
   return v
  g=d['main'].__globals__;g['read']=read
  g['time']=types.SimpleNamespace(time=time.time,monotonic=time.monotonic,sleep=lambda s:time.sleep(s*.003))
  d['main']();return d
 return original(path,*a,**kw)
runpy.run_path=run
run(str(N/'observe_actual.py'),run_name='__main__')
