import os,runpy,sys
from pathlib import Path
sys.path[:0]=[sys.argv[1]]
root,stage,source,sha,items,binding,kind=sys.argv[1:]
os.urandom=lambda n:bytes([17])*n
sys.argv=[root+'/build_d.py',stage,source,sha,items,binding]
if kind=='native':runpy.run_path(root+'/build_d.py',run_name='__main__')
else:
 sys.argv=[root+'/pack_token.py','--kind','d','--source',root+'/build_d.py']+(['--enable-token','--token',kind] if kind!='default' else [])+['--']+sys.argv[1:]
 runpy.run_path(root+'/pack_token.py',run_name='__main__')
