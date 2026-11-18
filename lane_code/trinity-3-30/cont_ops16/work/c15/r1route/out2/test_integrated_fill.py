"""Run fill and the actual metadata checker together under Python 3.6."""
from pathlib import Path
import json,shutil,subprocess,hashlib,ast
import fixture_fill as F
W=Path(__file__).resolve().parent
proofs=[]
for kind in ('A','B'):
 root,filled,result=F.fixture(kind);assert result.returncode==0,result.stderr
 proof=json.loads((root/'proof.json').read_text());assert proof['real_receipt'] is True and proof['synthetic_data_receipt'] is True
 original=W/kind;token=(original/'TOKEN').read_text().strip();p=root/('a15_cot_ap'+token)
 shutil.copytree(original/'package',p);p.joinpath('a').chmod(0o700)
 # Reseal only a disposable fixture copy to the explicitly synthetic data receipt.
 import io,tarfile
 with tarfile.open(p/'0.tgz') as t:payload={m.name:t.extractfile(m).read() for m in t}
 cfg=json.loads(payload['9.json']);cfg['export_binding']=proof['binding'];payload['9.json']=json.dumps(cfg,sort_keys=True).encode()
 (p/'0.tgz').write_bytes(F.tarbytes(payload));public=json.loads((p/'0.json').read_text());public.update(payload_bytes=(p/'0.tgz').stat().st_size,payload_sha256=F.pin((p/'0.tgz').read_bytes())['sha256'],plan_sha256=hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode()).hexdigest())
 (p/'0.json').write_text(json.dumps(public));(p/'CONFIG.json').write_text(json.dumps(public))
 manifest=json.loads((p/'PACKAGE.json').read_text())
 for n in ('0.tgz','0.json','CONFIG.json'):manifest['files'][n]=F.pin((p/n).read_bytes())['sha256']
 (p/'PACKAGE.json').write_text(json.dumps(manifest))
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
 assert r.returncode==0,r.stderr.decode();proofs.append(dict(package=kind,passed=True,real_config_and_receipt=True,synthetic_data_receipt=True,fixture_payload_resealed=True,fixture=str(root),metadata_check=json.loads(r.stdout),mocked=['Orchard package placement','sizes of unchanged non-export dependency archives'],real=['Python 3.6 helper execution','four-part scan and hash','real config and S1 receipt; synthetic data receipt','artifact binding','export admission','new archive file sizes']))
 # The inherited scan and preparation functions must be AST-identical.
 def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
 base=funcs(W/'bases'/('b1' if kind=='A' else 'b2')/'fill_export.py');now=funcs(original/'fill_export.py')
 assert all(base[n]==now[n] for n in ('scan','preparation'))
(W/'INTEGRATED_FILL.json').write_text(json.dumps(proofs,indent=2)+'\n');print('2 integrated fill/check proofs passed; scan and preparation checks unchanged')
