"""Run sealed sources with path mapping and a transparent, masked HTTP observer."""
import os,sys,re,json,runpy,subprocess,http.client,time,traceback
from pathlib import Path
O=Path(os.environ['TG_OUT']);K=Path(os.environ['TG_KIT']);X=O/'x'
a=sys.argv[1:]
while a and a[0].startswith('-'):a.pop(0)
script=Path(a[0]);sys.argv=a
def mask(s):return re.sub(r'https?://[^\s\"\'<>]+','[URL]',str(s))
class Masked:
 def __init__(self,f):self.f=f
 def write(self,s):self.f.write(mask(s));self.f.flush()
 def flush(self):self.f.flush()
if script.name=='gc.py' or '--writer' in a:
 sys.stdout=Masked((O/'logs/gc.stdout').open('a'));sys.stderr=Masked((O/'logs/gc.stderr').open('a'))
Original=http.client.HTTPSConnection
_gr=Original.getresponse
def _getresponse(self):
 try:
  r=_gr(self)
  with (O/'logs/http.jsonl').open('a') as f:f.write(json.dumps(dict(time=time.time(),http=r.status,range=r.getheader('Range')))+'\n')
  return r
 except Exception as e:
  with (O/'logs/http.jsonl').open('a') as f:f.write(json.dumps(dict(time=time.time(),error=mask(repr(e))))+'\n')
  raise
Original.getresponse=_getresponse
assert http.client.HTTPSConnection is Original
Original('example.invalid',443,timeout=1).close()
sys.path.insert(0,str(K/'b'))
import z
old=z.load
def load(p):
 v=old(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
z.load=load
original=subprocess.run
def run(argv,*a,**kw):
 if isinstance(argv,list) and any(str(K/'b'/v) in argv for v in ('pc.py','gc.py','o.py')):
  i=min(argv.index(str(K/'b'/v)) for v in ('pc.py','gc.py','o.py') if str(K/'b'/v) in argv);argv=argv[:i]+[str(Path(os.environ['TG_DIR'])/'observe.py')]+argv[i:]
 return original(argv,*a,**kw)
subprocess.run=run
try:
 if script.name=='pc.py':
  d=runpy.run_path(str(script),run_name='case_pc');oldread=d['read']
  def read(p):
   v=oldread(p)
   if Path(p).name=='p.json':v['n_root']=str(X)
   return v
  d['main'].__globals__['read']=read
  if '--writer' in a:raise SystemExit(d['writer_main'](a[a.index('--writer')+1:]))
  elif '--seconds' in a:print(max(1,int(d['deadline']()-time.time())))
  else:d['main']()
 else:runpy.run_path(str(script),run_name='__main__')
except SystemExit:
 raise
except BaseException:
 sys.stderr.write(mask(traceback.format_exc()));raise SystemExit(1)
