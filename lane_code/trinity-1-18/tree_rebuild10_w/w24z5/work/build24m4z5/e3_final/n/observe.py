import sys,os,runpy,http.client,json,hashlib,base64,time,types
from pathlib import Path
N=Path(os.environ['E3_N']);K=N/'k';X=N.parent/'x'
sys.path.insert(0,str(K/'b'))
import z
oldload=z.load
def load(p):
 v=oldload(p)
 if Path(p).name=='p.json':v['n_root']=str(X)
 return v
z.load=load
import importlib.util
spec=importlib.util.spec_from_file_location('q_transport',str(N.parents[1]/'transport.py'))
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
Connection=transport.Connection
os.environ['FAKE_SINK']=str(N/'sink')
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
  g['time']=types.SimpleNamespace(time=time.time,monotonic=lambda:time.monotonic()/.003,sleep=lambda s:time.sleep(s*.003))
  d['main']();return d
 return original(path,*a,**kw)
runpy.run_path=run
run(str(N/'observe_actual.py'),run_name='__main__')
