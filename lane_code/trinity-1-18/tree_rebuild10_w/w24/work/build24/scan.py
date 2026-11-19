from pathlib import Path
import ast,importlib.util,json,sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24'
sys.path[:0]=[str(D),str(L/'work/build21'),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.p3_provenance import digest
results={}
for name in ('q','n'):
    k=D/'kits'/name
    s=(L/'work/build22/naming22.py').read_text();tree=ast.parse(s)
    node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE_SEALS' for t in n.targets))
    pins={(doc,key):digest(J.load(k/doc)[key]) for doc in ('k/7.json','k/c0.json') for key in ('files','sources','operation_sources')}
    lines=s.splitlines();s='\n'.join(lines[:node.lineno-1]+['SOURCE_SEALS='+repr(pins)]+lines[node.end_lineno:])+'\n'
    old='u/825c26fd4f9e37d839b298ad83c4ea26e69403659de4c0a2de0e93c1678671c5'
    s=s.replace(old,J.load(k/'k/c.json')['r1_training']['mix']['path'])
    p=D/('naming24_'+name+'.py');p.write_text(s)
    spec=importlib.util.spec_from_file_location('naming24_'+name,p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    import environment21f as E
    certificate=J.load(L/'work/build21/environment_shell21g.json')
    if name=='n':
        original=(D/'kits/q/job.sh').read_text();actual=(k/'job.sh').read_text()
        assert actual==original.replace('--partition=general','--partition=advanced').replace('--gres=gpu:1','--gres=gpu:4')
        certificate['job.sh']['sha256']=J.sha(k/'job.sh')
    certdir=D/'scanners'/name;certdir.mkdir(parents=True,exist_ok=True)
    J.write(certdir/'environment_shell21g.json',certificate)
    (certdir/'environment21f.py').write_bytes((L/'work/build21/environment21f.py').read_bytes())
    with patch.object(E,'__file__',str(certdir/'environment21f.py')):
        results[name]=module.scan_decoded(k)
    results[name]['kit_seal']=J.seal(k)
    J.write(D/('SCAN_'+name+'.json'),results[name])
    print(name,results[name]['status'],results[name]['checked_strings'])
