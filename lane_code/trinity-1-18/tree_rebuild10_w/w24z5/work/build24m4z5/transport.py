"""Filesystem-backed GCS range protocol for offline tests only."""
import os,json,hashlib,base64
from pathlib import Path
class Reply:
 def __init__(self,status,raw=b'',headers=None):self.status=status;self.raw=raw;self.headers=headers or {}
 def read(self,*a,**kw):return self.raw
 def getheader(self,n):return self.headers.get(n)
class Connection:
 def __init__(self,*a,**kw):self.data=bytearray();self.headers={}
 def putrequest(self,method,path):self.name=path.split('?')[0].lstrip('/')
 def putheader(self,k,v):self.headers[k]=v
 def endheaders(self):pass
 def send(self,data):self.data.extend(data)
 def close(self):pass
 def getresponse(self):
  sink=Path(os.environ['FAKE_SINK']);sink.mkdir(exist_ok=True)
  token=hashlib.sha256(self.name.encode()).hexdigest();p=sink/token
  ran=self.headers.get('Content-Range');total=int(ran.split('/')[-1]) if ran else len(self.data)
  previous=p.read_bytes() if p.exists() else b''
  if self.data:
   offset=int(ran.split()[1].split('-')[0]) if ran else 0
   assert len(previous)==offset,(len(previous),offset)
   p.write_bytes(previous+self.data);previous=p.read_bytes()
  with (sink.parent/'requests.jsonl').open('a') as f:f.write(json.dumps(dict(name=self.name,range=ran,sent=len(self.data)))+'\n')
  if len(previous)==total:
   raw=json.dumps(dict(size=str(total),md5Hash=base64.b64encode(hashlib.md5(previous).digest()).decode(),crc32c='fixture',name=self.name,generation='1')).encode()
   return Reply(200,raw)
  return Reply(308,headers={'Range':'bytes=0-'+str(len(previous)-1)} if previous else {})
