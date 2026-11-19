"""Run fill and the actual metadata checker together under Python 3.6."""
from pathlib import Path
import json,shutil,subprocess,hashlib,ast
import fixture_fill as F
W=Path(__file__).resolve().parent
proofs=[]
for kind in ('b1','b2'):
 root,filled,result=F.fixture(kind);assert result.returncode==0,result.stderr
 proof=json.loads((root/'proof.json').read_text());assert proof['real_receipt'] is True
 original=W/'out'/kind;token=(original/'TOKEN').read_text().strip();p=root/('a15_cot_ap'+token)
 shutil.copytree(original/'package',p);p.joinpath('a').chmod(0o700)
 inputs=json.loads((filled/'a/1.json').read_text());mapping={}
 for idx in (0,4):
  for j,part in enumerate(inputs['archives'][idx]['parts']):
   remote='/project/community/jjyeung/okh7/a15_cot_ap'+token+'/a/e/'+str(j if idx==0 else 4)
   mapping[remote]=part['path'];part['path']=remote
 (p/'a/1.json').write_text(json.dumps(inputs,sort_keys=True,indent=2)+'\n')
 (p/'a/export.json').write_bytes((filled/'a/export.json').read_bytes())
 (root/'map.json').write_text(json.dumps(mapping))
 script=root/'11.py';script.write_text('''import sys,json,tarfile,types\nfrom pathlib import Path\np=Path(sys.argv[1]);mapping=json.loads(Path(sys.argv[2]).read_text())\nwith tarfile.open(p/'0.tgz') as t:source=t.extractfile('8.py').read()\nm=types.ModuleType('fixture');m.__file__=str(p/'3.py');exec(compile(source,m.__file__,'exec'),m.__dict__)\nreal=Path;inputs=json.loads((p/'a/1.json').read_text());sizes={v['path']:v['bytes'] for a in inputs['archives'] for v in a['parts']}\ndef path(v):\n if str(v)=='/project/community/jjyeung/okh7':return p.parent\n if str(v) in mapping:return real(mapping[str(v)])\n if str(v) in sizes:return types.SimpleNamespace(stat=lambda:types.SimpleNamespace(st_size=sizes[str(v)]))\n return real(v)\nm.Path=path\nv=m.check(p,1,'05:00:00');assert v['passed'] is True\nprint(json.dumps(v))\n''')
 r=subprocess.run(['/usr/bin/python3','-I','-s','-B',str(script),str(p),str(root/'map.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert r.returncode==0,r.stderr.decode();proofs.append(dict(package=kind,passed=True,real_preparation=True,fixture=str(root),metadata_check=json.loads(r.stdout),mocked=['Orchard package placement','sizes of unchanged non-export dependency archives'],real=['Python 3.6 helper execution','four-part scan and hash','real preparation pins','artifact binding','export admission','new archive file sizes']))
 # The inherited scan and preparation functions must be AST-identical.
 def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
 base=funcs(Path('/scratch/jjyeung/orch_n30/reader_r1/work/fix7')/kind/'fill_export.py');now=funcs(original/'fill_export.py')
 assert all(base[n]==now[n] for n in ('scan','preparation'))
(W/'out/INTEGRATED_FILL.json').write_text(json.dumps(proofs,indent=2)+'\n');print('2 integrated fill/check proofs passed; scan and preparation checks unchanged')
