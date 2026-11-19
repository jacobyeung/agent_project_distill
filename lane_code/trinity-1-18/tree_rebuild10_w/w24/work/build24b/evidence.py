from pathlib import Path
import ast,difflib,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24b';T=L/'work/tree_r1';A=L/'attic/build24b/tree';sys.path.insert(0,str(L/'work/build24'));import joblib as J
from importlib.util import spec_from_file_location,module_from_spec
changes={};diff=[]
for p in A.rglob('*.py'):
 name=str(p.relative_to(A));a=p.read_text();b=(T/name).read_text();lines=set()
 for tag,i,j,k,m in difflib.SequenceMatcher(a=a.splitlines(),b=b.splitlines(),autojunk=False).get_opcodes():
  if tag!='equal':lines.update(range(k+1,m+1))
 statements={n.lineno for n in ast.walk(ast.parse(b)) if isinstance(n,ast.stmt) and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))}
 changes[name]=dict(before=J.sha(p),after=J.sha(T/name),statements=sorted(lines&statements))
 diff.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='build24/'+name,tofile='build24b/'+name))
folders=[D/'proofs/proof_control',D/'proofs/init',D/'proofs/capacity',D/'proofs/tests23b/unit',L/'work/build21/proofs/final_focused',L/'work/build21/proofs/edges',L/'work/build21/proofs/producer_edges',L/'work/build22/proofs/new_tests']
hits={n:set() for n in changes};evidence=[]
for folder in folders:
 if not (folder/'source_hashes.json').exists():continue
 hashes=J.load(folder/'source_hashes.json');records=J.load(folder/'hits.json');evidence.append(str(folder.relative_to(L)))
 for name,c in changes.items():
  if hashes.get(name)==c['after']:hits[name].update(records.get(name,[]))
for name,c in changes.items():c.update(hit=sorted(set(c['statements'])&hits[name]),uncovered=sorted(set(c['statements'])-hits[name]))
J.write(D/'TREE_CHANGES.json',changes);(D/'TREE_CHANGES.diff').write_text(''.join(diff));J.write(D/'COVERAGE.json',dict(files=changes,total=sum(len(x['statements']) for x in changes.values()),covered=sum(len(x['hit']) for x in changes.values()),evidence=evidence))
proof=J.load(D/'proofs/capacity/RESULT.json');assert proof['status']=='ADMIT';assert proof['tree_sha256']==J.load(L/'out/TREE_SEAL.json')['tree_sha256']
rows={}
for name,value in proof['kits'].items():
 assert value['init_milestone']==400 and value['training_start_step']==(0 if name=='n' else 400)
 assert value['records']==288 and all(x==0 for x in value['deferred_cells'].values())
 assert value['direction_rows']==39971 and len(value['twins'])==8 and all(x['status']=='REFUSE' for x in value['twins'].values())
 cfg=J.load(value['config']['path']);receipt=J.load(cfg['preparation']['path']);statuses={k:v['status'] for k,v in receipt['component_evidence'].items()}
 assert sum(v=='DEFERRED' for v in statuses.values())==7 and sum(v=='NOT_PRESENT' for v in statuses.values())==2
 rows[name]=dict(status='ADMIT',init_milestone=400,training_start_step=value['training_start_step'],first_losses=value['first_losses'],records=288,
  refusal_twins=8,direction_rows=39971,deferred_cells=value['deferred_cells'],component_statuses=statuses,
  empty_optimizer=value['optimizer_state_entries']==0 if name=='n' else None)
J.write(D/'CPU_SUMMARY.json',dict(status='PASS',kits=rows,named_removals=proof['named_removals'],tree_sha256=proof['tree_sha256'],new_databases=0))
print('Tree changes',len(changes),'coverage',sum(len(x['hit']) for x in changes.values()),'/',sum(len(x['statements']) for x in changes.values()))
