import os,sys,runpy,http.client,concurrent.futures
from pathlib import Path
sys.path.insert(0,'/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/work/build24m4z12')
from strict_sink import Connection
__import__('strict_sink').install()
os.environ['STRICT_SESSIONS']=sys.argv[2]
os.environ['STRICT_SINK']=os.environ.get('FAKE_SINK',str(Path(sys.argv[2]).parent/'objects'))
kit=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n')
if os.environ.get('STRICT_OLD')=='1':
 d=runpy.run_path(str(kit/'b/gc.py'),run_name='gc_runtime')
 d['main'].__globals__['ProcessPoolExecutor']=concurrent.futures.ThreadPoolExecutor
 raise SystemExit(d['main'](sys.argv[1:]))
d=runpy.run_path(str(kit/'b/pc.py'),run_name='pc_runtime')
raise SystemExit(d['writer_main']([str(kit/'b/gc.py'),*sys.argv[1:]]))
