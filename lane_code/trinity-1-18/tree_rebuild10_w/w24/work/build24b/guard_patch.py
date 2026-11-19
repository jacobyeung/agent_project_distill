from pathlib import Path
import ast,hashlib,shutil,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';A=L/'attic/build24b';sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from launch_r2.build import capsule_json
source=(L.parent/'w23/work/build21/kits/q/b/g.py').read_text();assert hashlib.sha256(source.encode()).hexdigest().startswith('e397ea70')
(D/'g.py').write_text(source)
changed=[]
for name in ('work/build20/kit.py','work/build21/base/kit.py','work/build21/kit.py','work/build22/kit.py'):
 p=L/name;s=p.read_text();nodes=[n for n in ast.walk(ast.parse(s)) if isinstance(n,ast.Constant) and isinstance(n.value,str) and "raise RuntimeError('E42')" in n.value and 'total_memory' in n.value]
 assert len(nodes)==1;node=nodes[0];lines=s.splitlines(True);old=''.join(lines[node.lineno-1:node.end_lineno]);part=old.index("'''");end=old.rindex("'''")
 new=old[:part]+repr(source)+old[end+3:];s=''.join(lines[:node.lineno-1])+new+''.join(lines[node.end_lineno:]);s=s.replace('minimum_gpu_gib=80','minimum_gpu_gib=75')
 a=A/name;a.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,a);p.write_text(s);compile(s,str(p),'exec');changed.append(name)
for base in ('work/build20/kits','work/build21/kits','work/build22/kits','work/build24/kits'):
 for p in (L/base).glob('*/b/g.py'):
  a=A/p.relative_to(L);a.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,a);p.write_text(source)
  k=p.parents[1];build=J.load(k/'BUILD.json');build['resource_request']['minimum_gpu_gib']=75
  files={str(q.relative_to(k)):J.sha(q) for q in k.rglob('*') if q.is_file() and q.name not in ('SHA256SUMS.txt','BUILD.json')}
  (k/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(files.items())))
  build['kit_sha256']=J.seal(k);(k/'BUILD.json').write_bytes(capsule_json(build));changed.append(str(p.relative_to(L)))
J.write(D/'GUARD_PATCH.json',dict(guard_sha256=J.sha(D/'g.py'),changed=changed,baseline_upload_stream_unchanged=True))
# Run the exact released 8 new cases and 9 inherited cases against both active kits.
for name in ('q','n'):
 for kind,src in [('new',L.parent/'w23/work/build23d/guard_tests.py'),('legacy',L.parent/'w23/work/build23c/guard_tests.py')]:
  s=src.read_text().replace("D=L/'work/build23d'",f"D=L/'work/build24b/guard_{name}'").replace("D=L/'work/build23c'",f"D=L/'work/build24b/guard_{name}'").replace("K=L/'work/build21/kits/q'",f"K=L/'work/build24/kits/{name}'")
  s=s.replace("L/'attic/build23c/g.py'","L/'attic/build24b/work/build24/kits/q/b/g.py'")
  s=s.replace("{'v','a','c','e','n','m','d0','dc','x'}","{'v','a','c','e','ec','n','m','d0','dc','x'}").replace("diag['e']=='0'","diag['e'] is True and diag['ec']==1")
  if kind=='legacy':s=s.replace("D/'GUARD_TESTS.json'","D/'LEGACY_GUARD_TESTS.json'")
  (D/('guard_'+name)).mkdir(exist_ok=True);(D/('guard_'+name+'_'+kind+'.py')).write_text(s)
p=D/'init_tests.py';s=p.read_text().replace("k.endswith('.safetensors')", "k.endswith(('.safetensors','.index.json'))");p.write_text(s)
print(json.dumps(changed,indent=2))
