import os,runpy,sys
root,stage,source,sha,items,binding,kind,adapter=sys.argv[1:]
sys.path.insert(0,root);os.urandom=lambda n:bytes([17])*n
sys.argv=[root+'/build_d.py',stage,source,sha,items,binding]
if kind=='native':runpy.run_path(root+'/build_d.py',run_name='__main__')
else:
 sys.argv=[adapter,'--kind','d','--source',root+'/build_d.py']+(['--enable-token','--token',kind] if kind!='default' else [])+['--']+sys.argv[1:]
 runpy.run_path(adapter,run_name='__main__')
