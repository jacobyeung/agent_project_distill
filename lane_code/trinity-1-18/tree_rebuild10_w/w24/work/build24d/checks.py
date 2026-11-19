from pathlib import Path
import ast,base64,hashlib,importlib.util,json,re,sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24d'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1')]
import joblib as J,environment21f as E
from student_pilot.p3_provenance import digest
from launch_r1.build import verify

for name in ('q','n','n_go'):
 k=L/'out/kit_n_go' if name=='n_go' else L/'work/build24/kits'/name;cert={};starts=[]
 for p in [*sorted(k.rglob('*.sh')),k/'k/j.json']:
  source=p.read_text()
  if p.suffix=='.json':source=base64.b64decode(json.loads(source)['payload']).decode()
  assert 'PYTHONDONTWRITEBYTECODE=1' in source
  bindings=[]
  for num,line in enumerate(source.splitlines(),1):
   if re.search(r'(?<![\w/])(?:/usr/bin/)?python3\s|"\$PILOT_VENV/bin/python"\s|exec "\$PY"',line):
    for m in re.finditer(r'(?:/usr/bin/python3|\bpython3|"\$PILOT_VENV/bin/python"|"\$PY")\s+([^\n|;]*)',line):
     assert '-B' in m.group(1).split(),(p,num,line)
     starts.append(dict(path=str(p.relative_to(k)),line=num,command=line))
   names=set(re.findall(r'(?<![\w$])([A-Za-z_]\w*)=(?!=)',line))
   for pattern in (r'\bfor\s+([A-Za-z_]\w*)\s+in\b',r'\bread -r ([A-Za-z_][\w ]*)',r'^\s*local ([A-Za-z_][\w ]*)$',r'\bexport ([A-Z_][A-Z_0-9]*)(?: |$)'):
    match=re.search(pattern,line)
    if match:names.update(match.group(1).split())
   if names:bindings.append(dict(line=num,names=sorted(names),expression=line))
  cert[str(p.relative_to(k))]=dict(sha256=hashlib.sha256(source.encode()).hexdigest(),runtime_literal_names=sorted({x for r in bindings for x in r['names']}),bindings=bindings,reason='Reviewed fixed literal assignments; only local runtime directories and bytecode flags changed. Any source edit invalidates this certificate.')
 certdir=D/'scanners'/name;certdir.mkdir(parents=True,exist_ok=True)
 J.write(certdir/'environment_shell21g.json',cert)
 (certdir/'environment21f.py').write_bytes((L/'work/build21/environment21f.py').read_bytes())
 source=(L/'work/build22/naming22.py').read_text();tree=ast.parse(source)
 node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE_SEALS' for t in n.targets))
 pins={(doc,key):digest(J.load(k/doc)[key]) for doc in ('k/7.json','k/c0.json') for key in ('files','sources','operation_sources')}
 lines=source.splitlines();source='\n'.join(lines[:node.lineno-1]+['SOURCE_SEALS='+repr(pins)]+lines[node.end_lineno:])+'\n'
 source=source.replace('u/825c26fd4f9e37d839b298ad83c4ea26e69403659de4c0a2de0e93c1678671c5',J.load(k/'k/c.json')['r1_training']['mix']['path'])
 p=D/('naming24d_'+name+'.py');p.write_text(source)
 spec=importlib.util.spec_from_file_location('naming24d_'+name,p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 with patch.object(E,'__file__',str(certdir/'environment21f.py')):result=module.scan_decoded(k)
 result['kit_seal']=verify(k);J.write(D/('SCAN_'+name+'.json'),result)
 J.write(D/('STARTS_'+name+'.json'),starts)
 print(name,result['status'],len(starts),'guarded shell Python starts',flush=True)
