from pathlib import Path
import importlib.util,os,json
from types import SimpleNamespace
from unittest.mock import patch
J=Path.cwd();D=J/'work/build24m4z5';K=J/'out/kit_n'
s=importlib.util.spec_from_file_location('pc_owner',K/'b/pc.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
r=D/'owner';r.mkdir();k=r/'k';(k/'k').mkdir(parents=True);x=r/'x';(x/'n_s').mkdir(parents=True,mode=0o700);n=r/'n'
for name in ('n','y'):(k/('k/'+name+'.json')).write_bytes((K/('k/'+name+'.json')).read_bytes())
C.put(k/'k/p.json',dict(n_root=str(x)))
C.put(x/'n_s/sess_41.json',{v+'.j41'+f'.part{i:02d}-of-04':'https://local.invalid/'+str(i) for v in C.read(k/'k/y.json')['objects'].values() for i in range(4)})
c=C.Copier(k,n,'41');original=os.fstat;calls=[]
def fstat(fd):
 v=original(fd);calls.append(fd)
 if len(calls)==2:return SimpleNamespace(st_uid=os.getuid()+1,st_dev=v.st_dev,st_ino=v.st_ino,st_mode=v.st_mode)
 return v
with patch.object(C.os,'fstat',side_effect=fstat):
 try:c.session_bytes(c.spool/'private/sess.json')
 except ValueError as e:assert str(e)=='file owner'
 else:raise AssertionError('wrong cached-file owner accepted')
(D/'OWNER.json').write_text(json.dumps(dict(status='PASS',cached_file_owner_checked=True))+'\n');print('PASS: cached file owner refuses')
