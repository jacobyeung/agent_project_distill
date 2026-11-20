import sys,os,runpy,json,importlib.util,hashlib,base64
from pathlib import Path
W=Path(__file__).resolve().parent;K=W/'kit';sys.path.insert(0,str(K/'b'))
import z
original=z.load
def load(p):
 v=original(p)
 if Path(p).name=='p.json':v['n_root']=os.environ['TEST_X']
 return v
z.load=load
script=sys.argv[1];sys.argv=sys.argv[1:]
if Path(script).name=='pc.py':
 d=runpy.run_path(script,run_name='case_pc'); old=d['read']
 def read(p):
  v=old(p)
  if Path(p).name=='p.json':v['n_root']=os.environ['TEST_X']
  return v
 d['Copier'].__init__.__globals__['read']=read
 d['main'].__globals__['read']=read
 d['main']()
else:runpy.run_path(script,run_name='__main__')
