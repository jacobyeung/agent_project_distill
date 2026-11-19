from pathlib import Path
import io,os,shutil,subprocess,sys,tarfile,json,shlex
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from launch_r1.build import verify
records={}
for name in ('q','n'):
 k=D/'before'/name;k.parent.mkdir(exist_ok=True);shutil.copytree(L/'work/build24/kits'/name,k)
 r=D/'before'/('node_'+name);r.mkdir()
 a=r/'s.tar'
 with tarfile.open(a,'w') as t:
  raw=b'{}';i=tarfile.TarInfo('a/snapshots/abc/config.json');i.size=len(raw);t.addfile(i,io.BytesIO(raw))
 before={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()};verify(k)
 shell=(D/('j_'+name+'_before.sh')).read_text()
 line=next(x.strip() for x in shell.splitlines() if '"$Q_KIT/b/m.py"' in x).replace('/usr/bin/python3',sys.executable)
 env={**os.environ,'Q_KIT':str(k),'file':str(a),'sha':J.sha(a),'snap':str(r/'snap'),'REV':'abc','PYTHONDONTWRITEBYTECODE':'1'}
 result=subprocess.run(['/bin/bash','-c',line],env=env,cwd=r,capture_output=True,text=True)
 assert result.returncode==0,result.stderr
 # Later log-screen imports run in the normal exported environment.
 log=next(x for x in shell.splitlines() if '"$Q_KIT/b/a.py"' in x).split('|',1)[1].split('>',1)[0].replace('/usr/bin/python3',sys.executable)
 p=subprocess.run(['/bin/bash','-c',log],env=env,cwd=r,input='fixture\n',capture_output=True,text=True);assert p.returncode==0
 after={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
 try:verify(k)
 except ValueError as e:error=str(e)
 else:raise AssertionError('Expected content refusal')
 assert error=='R1_KIT_CONTENT_DIFFERS'
 added=sorted(set(after)-set(before));assert any(x.startswith('b/__pycache__/z.') for x in added)
 records[name]=dict(status='REPRODUCED',error=error,added=added,command=line,environment={'PYTHONDONTWRITEBYTECODE':'1'},cause='Staging helper -I ignores PYTHON* environment; missing -B permits z.py bytecode')
J.write(D/'BEFORE.json',records);print(json.dumps(records,indent=2))
