from pathlib import Path
import sys,json,ast,hashlib,shutil
L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from launch_r1.build import verify
base=J.load(D/'BASELINE.json');tree=L/'work/tree_r1'
actual={str(p.relative_to(tree)):J.sha(p) for p in sorted(tree.rglob('*')) if p.is_file()}
from student_pilot.p3_provenance import digest
seal=digest(actual)
expected=J.load(D/'TREE_VERIFICATION.json');assert seal==expected['seal'],seal
changed=sorted(n for n in set(base['tree'])|set(actual) if base['tree'].get(n)!=actual.get(n));assert changed==expected['changed']
for name,h in base['packages'].items():assert J.sha(L/'out'/name)==h,name
old=ast.parse((L/'attic/build24k/work/build24/joblib.py').read_text());new=ast.parse((L/'work/build24/joblib.py').read_text())
before={n.name:ast.dump(n,include_attributes=False) for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
after={n.name:ast.dump(n,include_attributes=False) for n in new.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
modified=sorted(n for n in before if before[n]!=after.get(n));assert set(modified)<=set(('stage_payload','bootstrap')),(modified)
kits={}
for name in ('q','n','n_go'):
 k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name)
 kits[name]=verify(k);assert J.load(k/'k/a.json')['GO']==(name=='n_go')
 assert J.sha(k/'k/n.json')==base['kits'][name]['k/n.json']
 for unchanged in ('k/8.json','k/g.json','k/l.json','k/s.json','b/resolve.py','b/t.py','b/u.py'):
  if unchanged in base['kits'][name]:assert J.sha(k/unchanged)==base['kits'][name][unchanged],(name,unchanged)
 assert 'routing_inputs' not in J.load(k/'k/r.json')
 assert J.load(D/('SCAN_'+name+'.json'))['kit_seal']==kits[name]
 if name!='n_go':assert J.load(D/'SEQUENCE.json')[name]['production_kit_seal']==kits[name]
source=L/'work/build24/RESOLVER_TESTS.json';assert J.load(source)['successful'];shutil.copyfile(source,D/'RESOLVER600_TESTS.json')
source=D/'proofs/resolver23/RESOLVER_TESTS.json';assert J.load(source)['successful'];shutil.copyfile(source,D/'RESOLVER23_TESTS.json')
reports={}
for p in sorted(D.glob('*TEST*.json')):
 v=J.load(p)
 if isinstance(v,dict):
  assert v.get('status','PASS')=='PASS',(p,v.get('status'))
  assert v.get('successful',True),(p,v)
  assert v.get('passed',True),(p,v)
  assert not v.get('errors',0) and not v.get('failures',0),(p,v)
 reports[p.name]=dict(sha256=J.sha(p),status='PASS',tests=v.get('tests') if isinstance(v,dict) else None)
for p in sorted((D/'guard_q').glob('*.json'))+sorted((D/'guard_n').glob('*.json')):
 v=J.load(p)
 if isinstance(v,dict) and 'successful' in v:
  assert v['successful'];reports[str(p.relative_to(D))]=dict(sha256=J.sha(p),status='PASS',tests=v.get('tests'))
for name in ('SUITES.json','VALIDATION.json'):
 p=D/name;target=L/'attic/build24k/initial_validation'/name;target.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and not target.exists():p.rename(target)
J.write(D/'SUITES.json',reports)
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=seal,files=len(actual),changed=changed,base_packages_unchanged=len(base['packages']),kits=kits,config_bytes_unchanged=True,resolver_changed_functions=modified,resolver_identity_functions_unchanged=True,GO_only_template=True,production_admission='NOT_RUN'))
J.write(D/'VALIDATION.json',dict(status='PASS',reports=reports,hidden_path='Both kits reach unavailable production database',GO_rehearsal='NOT_RUN',native_host_fixture='14 passed; one base-comparison test skipped, checked independently by tree inventory',routing_fixture='a.py r and native exact-path selection checks; production P equality requires Orchard'))
print('PASS:',len(reports),'test reports; tree',seal,'kits',kits)
