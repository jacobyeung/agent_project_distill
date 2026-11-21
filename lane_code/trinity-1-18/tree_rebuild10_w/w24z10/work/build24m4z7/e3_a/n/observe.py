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
class Connection(Original):
 def getresponse(self):return Reply(super().getresponse())
http.client.HTTPSConnection=Connection
try:runpy.run_path(str(script),run_name='__main__')
except SystemExit:raise
except Exception as e:
 print(re.sub(r'https?://[^\s]+','[URL]',repr(e)),file=sys.stderr);raise SystemExit(1)
