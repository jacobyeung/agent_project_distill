"""Capture response fields without retaining capabilities or response errors."""
import sys,os,json,runpy,subprocess,http.client,time,hashlib
from pathlib import Path
N=Path(os.environ['E2_N']);K=N/'k'
args=sys.argv[1:]
while args and args[0].startswith('-'):args.pop(0)
script=Path(args[0]).resolve();sys.argv=args
if script not in {(K/'b'/n).resolve() for n in ('pc.py','gc.py','o.py','ep.py','sr.py')}:
 raise SystemExit(92)
sys.path.insert(0,str(K/'b'))
if script.name=='pc.py':
 original=subprocess.run
 def run(argv,*a,**kw):
  if isinstance(argv,list) and str(K/'b/gc.py') in argv:
   i=argv.index(str(K/'b/gc.py'))
   argv=argv[:i]+[str(N/'observe.py')]+argv[i:]
  return original(argv,*a,**kw)
 subprocess.run=run
if script.name=='gc.py':
 Original=http.client.HTTPSConnection
 class Reply:
  def __init__(self,r):self.r=r;self.status=r.status
  def read(self,*a,**kw):
   raw=self.r.read(*a,**kw)
   if self.status in (200,201):
    try:
     v=json.loads(raw)
     keep={k:v.get(k) for k in ('size','crc32c','md5Hash','name','generation')}
     p=N/'obs'/('r_'+str(os.getpid())+'_'+str(time.time_ns())+'.json')
     p.write_text(json.dumps(keep,sort_keys=True)+'\n')
    except (ValueError,OSError):pass
   return raw
  def __getattr__(self,n):return getattr(self.r,n)
 class Connection(Original):
  def getresponse(self):return Reply(super().getresponse())
 http.client.HTTPSConnection=Connection
# The kit sources run unchanged. Exceptions expose only their class to local logs.
try:runpy.run_path(str(script),run_name='__main__')
except SystemExit as e:
 if isinstance(e.code,str):print('E2_CHILD_FAIL',file=sys.stderr);raise SystemExit(1)
 raise
except Exception as e:
 print('E2_CHILD_FAIL '+type(e).__name__,file=sys.stderr);raise SystemExit(1)
