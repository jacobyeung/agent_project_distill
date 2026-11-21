import sys,os,json,runpy,subprocess,http.client,time,re
from pathlib import Path
N=Path(os.environ['E3_N']);K=N/'k';a=sys.argv[1:]
while a and a[0].startswith('-'):a.pop(0)
script=Path(a[0]).resolve();sys.argv=a
if script not in {(K/'b'/n).resolve() for n in ('pc.py','gc.py','o.py','ep.py','sr.py')}:raise SystemExit(92)
sys.path.insert(0,str(K/'b'))
original=subprocess.run
def run(argv,*args,**kw):
 if isinstance(argv,list) and any(str(K/'b'/v) in argv for v in ('pc.py','gc.py','o.py')):
  i=min(argv.index(str(K/'b'/v)) for v in ('pc.py','gc.py','o.py') if str(K/'b'/v) in argv)
  argv=argv[:i]+[str(N/'observe.py')]+argv[i:]
 return original(argv,*args,**kw)
subprocess.run=run
Original=http.client.HTTPSConnection
_getresponse=Original.getresponse
class Reply:
 def __init__(self,r):self.r=r;self.status=r.status
 def read(self,*a,**kw):
  raw=self.r.read(*a,**kw)
  if self.status in (200,201):
   try:
    v=json.loads(raw);keep={k:v.get(k) for k in ('size','crc32c','md5Hash','name','generation')}
    (N/'obs'/('r_'+str(os.getpid())+'_'+str(time.time_ns())+'.json')).write_text(json.dumps(keep)+'\n')
   except (ValueError,OSError):pass
  return raw
 def __getattr__(self,n):return getattr(self.r,n)
from urllib.parse import urlsplit
sessions=json.loads((N/'sess.json').read_text()) if (N/'sess.json').exists() else {}
paths={urlsplit(v).path+('?' +urlsplit(v).query if urlsplit(v).query else ''):k for k,v in sessions.items()}
_putrequest=Original.putrequest;_putheader=Original.putheader

def putrequest(self,method,path,*a,**kw):
 self._e3_name=paths.get(path,'');self._e3_cr=''
 return _putrequest(self,method,path,*a,**kw)
def putheader(self,name,*values):
 if name.lower()=='content-range':self._e3_cr=str(values[0])
 return _putheader(self,name,*values)
def getresponse(self):
 r=_getresponse(self);name=getattr(self,'_e3_name','');cr=getattr(self,'_e3_cr','')
 if '_ckstop.' in name and name.endswith('.part00-of-04'):
  ran=r.getheader('Range');flag=N/'obs/interrupted.json'
  def record(kind):
   with (N/'obs/resume.jsonl').open('a') as f:f.write(json.dumps(dict(kind=kind,name=name,http=r.status,range=ran,content_range=cr,time=time.time()))+'\n')
  if r.status==308 and ran and cr.startswith('bytes ') and not cr.startswith('bytes */') and not flag.exists():
   flag.write_text(json.dumps(dict(name=name,range=ran,time=time.time())));record('interrupted')
   r.read();self.close();raise ConnectionResetError('E3 controlled interruption after acknowledged prefix')
  if flag.exists():
   if r.status==308 and ran and cr.startswith('bytes */'):record('resume_status')
   elif not cr.startswith('bytes */'):record('resume_chunk')
 return Reply(r)
Original.putrequest=putrequest
Original.putheader=putheader
Original.getresponse=getresponse
# Constructor probe has no socket operation and guards stdlib class identity.
assert http.client.HTTPSConnection is Original
Original('example.invalid',443,timeout=1).close()
try:runpy.run_path(str(script),run_name='__main__')
except SystemExit:raise
except Exception as e:
 print(re.sub(r'https?://[^\s]+','[URL]',repr(e)),file=sys.stderr);raise SystemExit(1)
