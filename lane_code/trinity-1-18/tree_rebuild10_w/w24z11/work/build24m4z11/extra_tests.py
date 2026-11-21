from pathlib import Path
import ast,gzip,hashlib,json,shutil,sys,tempfile,traceback,subprocess
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4z11';sys.path.insert(0,str(L/'out'))
import arm_launch as C
from unittest.mock import patch
import environment21f as E
T=Path(tempfile.mkdtemp(prefix='.e_',dir=L));rows=[]
def refuse(name,call,expected):
 try:call()
 except Exception as error:
  output=traceback.format_exc();(D/(name+'.log')).write_text(output)
  assert expected in str(error),(name,str(error));rows.append(dict(case=name,status='OK',refusal=str(error)))
 else:raise AssertionError('accepted '+name)
try:
 k=T/'k';shutil.copytree(L/'out/kit_n',k)
 p=k/'b/pc.py';p.write_text(p.read_text()+'\n# changed\n')
 refuse('scanner_changed_program',lambda:C.arm.scan(k,'n'),'INHERITED_ENVIRONMENT_SOURCE_DIFFERS')
 frozen=ast.parse((L/'out/kit_n/b/pc.py').read_text());frozen.body.append(ast.Pass())
 refuse('scanner_changed_ast',lambda:E.scan_python(frozen,lambda *args:None,'b/pc.py'),'keyword expansion')
 refuse('scanner_unknown_environment',lambda:E.scan_python(ast.parse("import os\nos.environ[key]=value"),lambda *args:None,'b/new.py'),'environment key is not a literal')
 # The source-hash certificate does not authorize modified shell assignments.
 shell=(L/'out/kit_n/b/pc.sh').read_text()+'\nexport "$key=$value"\n'
 with patch.object(E,'__file__',str(L/'work/build24m4x2/scanners/n/environment21f.py')):
  refuse('scanner_changed_shell',lambda:E.scan_shell(shell,lambda *args:None,'b/pc.sh'),'ENV_UNRESOLVED')
 # Check actual recipe and GO payloads independently of wrapper assertions.
 result=json.loads((D/'TEST_RESULTS.json').read_text())
 for index,r in enumerate(result['run_attic']):
  root=Path(r)/'armed/kits';stop=(3600,6000)[index]
  for n in ('n','n_go'):
   assert C.J.load(root/n/'k/n.json')['recipe']['stop_before_seconds']==stop
   assert C.J.load(root/n/'k/a.json')['GO']==(n=='n_go')
   own=subprocess.run([sys.executable,'-I','-s','-B',str(root/n/'b/v.py'),str(root/n)],capture_output=True,text=True)
   assert own.returncode==0 and own.stdout.strip()==C.J.sha(root/n/'SHA256SUMS.txt'),own.stderr
  assert (root/'q/k/n.json').read_bytes()==(L/'work/build24/kits/q/k/n.json').read_bytes()
 rows.append(dict(case='recipes_go_native_checkers',status='OK'))
 print(json.dumps(dict(status='OK',tests=rows),sort_keys=True))
 C.write(D/'EXTRA_TESTS.json',dict(status='OK',tests=rows))
finally:T.rename(L/'attic/build24m4z11'/T.name)
