import sys,os,runpy,subprocess,time,types
from pathlib import Path
W=Path(__file__).resolve().parent;K=W/'kit'
sys.path.insert(0,str(K/'b'))
import z
original=z.load
def mapped(p):
 v=original(p)
 if Path(p).name=='p.json':v['n_root']=os.environ['TEST_X']
 return v
z.load=mapped
args=sys.argv[1:]
while args and args[0].startswith('-'):args.pop(0)
script=args[0];sys.argv=args
if Path(script).name=='pc.py':
 d=runpy.run_path(script,run_name='case_pc');old=d['read']
 def read(p):
  v=old(p)
  if Path(p).name=='p.json':v['n_root']=os.environ['TEST_X']
  return v
 g=d['main'].__globals__;g['read']=read
 # Accelerate only the copier polling clock; sealed bytes stay unchanged.
 g['time']=types.SimpleNamespace(time=time.time,monotonic=time.monotonic,sleep=lambda s:time.sleep(s*.003))
 run=subprocess.run
 def call(a,*args,**kw):
  if isinstance(a,list) and str(K/'b/gc.py') in a:
   a=list(a);a[a.index(str(K/'b/gc.py'))]=str(W/'fake_gc_run.py')
  return run(a,*args,**kw)
 subprocess.run=call
 d['main']()
else:runpy.run_path(script,run_name='__main__')
