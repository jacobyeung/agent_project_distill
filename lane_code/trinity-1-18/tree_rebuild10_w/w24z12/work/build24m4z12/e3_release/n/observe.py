import sys,os,runpy,http.client,time,types
from pathlib import Path
N=Path(os.environ['E3_N']);K=N/'k';X=N.parent/'x'
sys.path.insert(0,'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/work/build24m4z12')
from strict_sink import Connection
__import__("strict_sink").install()
if '--writer' in sys.argv:os.environ['STRICT_SESSIONS']=sys.argv[sys.argv.index('--writer')+3]
sys.path.insert(0,str(K/'b'))
import z
oldload=z.load
def load(p):
 v=oldload(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
z.load=load
original=runpy.run_path
def run(path,*a,**kw):
 if Path(path).name=='pc.py':
  d=original(path,run_name='case_pc');g=d['main'].__globals__;old=g['read']
  def read(p):
   v=old(p)
   if Path(p).name=='p.json':v['n_root']=str(X)
   return v
  g['read']=read;g['deadline']=lambda:time.time()+5;g['ARCHIVE_SECONDS']=1
  g['time']=types.SimpleNamespace(time=time.time,monotonic=lambda:time.monotonic()/.003,sleep=lambda s:time.sleep(s*.003))
  if '--writer' in sys.argv:raise SystemExit(d['writer_main'](sys.argv[sys.argv.index('--writer')+1:]))
  elif '--seconds' in sys.argv:print(6)
  else:d['main']()
  return d
 return original(path,*a,**kw)
runpy.run_path=run
run(str(N/'observe_actual.py'),run_name='__main__')
