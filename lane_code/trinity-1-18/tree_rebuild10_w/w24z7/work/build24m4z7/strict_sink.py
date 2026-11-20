"""Offline resumable protocol fixture; no sockets and no capability logs."""
import base64,hashlib,json,os,re,threading,time
from pathlib import Path
LOCK=threading.Lock()
class Reply:
 def __init__(self,status,body=b'',headers=None):self.status=status;self.body=body;self.headers=headers or {}
 def read(self,*a,**kw):return self.body
 def getheader(self,name,default=None):return self.headers.get(name,default)
class Connection:
 def __init__(self,*a,**kw):self.headers={};self.data=bytearray();self.timeout=kw.get('timeout',10)
 def putrequest(self,method,path,*a,**kw):self.method=method;self.path=path
 def putheader(self,name,value):self.headers[name.lower()]=str(value)
 def endheaders(self):pass
 def send(self,data):self.data.extend(data)
 def close(self):pass
 def getresponse(self):
  with LOCK:return self.respond()
 def respond(self):
  from urllib.parse import urlsplit
  sessions=json.loads(Path(os.environ['STRICT_SESSIONS']).read_text())
  names={urlsplit(v).path+('?' +urlsplit(v).query if urlsplit(v).query else ''):k for k,v in sessions.items()}
  name=names.get(self.path.rstrip('?')) or names.get(self.path)
  root=Path(os.environ['STRICT_SINK']);root.mkdir(exist_ok=True)
  token=hashlib.sha256(str(name).encode()).hexdigest();p=root/(token+'.data');meta=root/(token+'.json')
  data=p.read_bytes() if p.exists() else b''
  headers={'Range':'bytes=0-'+str(len(data)-1)} if data else {}
  def reply(code,body=b''):
   row=dict(name=name,http=code,range=headers.get('Range'),content_range=self.headers.get('content-range'),bytes=len(self.data))
   with (root/'events.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
   return Reply(code,body,headers)
  if not name or self.method!='PUT' or self.headers.get('content-length')!=str(len(self.data)):return reply(400)
  cr=self.headers.get('content-range','')
  if meta.exists():
   if cr.startswith('bytes */') and not self.data:return reply(200,meta.read_bytes())
   return reply(409)
  if cr.startswith('bytes */') and not self.data:
   if cr=='bytes */0':
    v=dict(name=name,size='0',md5Hash=base64.b64encode(hashlib.md5(b'').digest()).decode(),crc32c='AAAAAA==',generation='1')
    p.write_bytes(b'');meta.write_text(json.dumps(v));return reply(200,meta.read_bytes())
   return reply(308)
  match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',cr)
  if not match:return reply(400)
  first,last,total=map(int,match.groups())
  if first!=len(data) or last-first+1!=len(self.data) or last>=total:return reply(400)
  if last+1<total and len(self.data)%(256<<10):return reply(400)
  mode=os.environ.get('STRICT_FAIL','')
  selected=os.environ.get('STRICT_SELECT','ckstop')
  if selected in name and mode=='once' and not (root/'failed_once').exists():
   (root/'failed_once').write_text('1');return reply(503)
  if selected in name and mode=='fail':return reply(503)
  if selected in name and mode=='block':time.sleep(5);raise TimeoutError('fixture blocked')
  if selected in name and mode=='stall':
   time.sleep(.3);raise TimeoutError('fixture stalled [URL]')
  if selected in name and mode=='partial' and data:return reply(503)
  data+=bytes(self.data);p.write_bytes(data)
  headers={'Range':'bytes=0-'+str(len(data)-1)}
  if len(data)<total:return reply(308)
  v=dict(name=name,size=str(total),md5Hash=base64.b64encode(hashlib.md5(data).digest()).decode(),crc32c='fixture',generation='1')
  meta.write_text(json.dumps(v))
  if selected in name and mode=='lost' and not (root/(token+'.lost')).exists():
   (root/(token+'.lost')).write_text('1');raise ConnectionResetError('fixture lost final response')
  return reply(200,meta.read_bytes())
