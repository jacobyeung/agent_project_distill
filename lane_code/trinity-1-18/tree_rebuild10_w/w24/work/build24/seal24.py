from pathlib import Path
import ast,difflib,hashlib,json,os,sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24';T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'))
sys.path[:0]=[str(D),str(T)];import joblib as J
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
files=inventory(T);changed={};patches=[]
with tarfile.open(L.parent/'w22/out/tree_rebuild_b22_d41a6dc8.tar') as tar:
 for name,h in files.items():
  try:raw=tar.extractfile('work/tree_r1/'+name).read()
  except KeyError:raw=b''
  before=hashlib.sha256(raw).hexdigest()
  if before==h:continue
  s=(T/name).read_text();a=raw.decode().splitlines();b=s.splitlines();lines=set()
  for tag,i,j,k,m in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():
   if tag!='equal':lines.update(range(k+1,m+1))
  statements={n.lineno for n in ast.walk(ast.parse(s)) if isinstance(n,ast.stmt)} if name.endswith('.py') else set()
  changed[name]=dict(before=before,after=h,changed_statements=sorted(lines&statements))
  patches.extend(difflib.unified_diff(a,b,fromfile='build22/'+name,tofile='build24/'+name,lineterm=''))
assert set(changed)=={'launch_r1/build.py','launch_r1/entry.py','launch_r1/production_proof.py','student_pilot/r1_coverage.py','student_pilot/r1_population.py','student_pilot/r1_rooms.py','student_pilot/s1_admission.py'}
J.write(D/'TREE_CHANGES.json',changed);(D/'TREE_CHANGES.diff').write_text('\n'.join(patches)+'\n')
assert files==J.load(D/'TREE_FILES.json');assert digest(files)==J.load(L/'out/TREE_SEAL.json')['tree_sha256']
# Identity functions retain all established checks. Only the requested artifact
# milestone comparison now reads the sealed spec's exact 400/600 step.
old=ast.parse((L/'attic/build24/joblib23.py').read_text());new=ast.parse((D/'joblib.py').read_text().replace("artifact.get('step')!=spec.get('step',400)","artifact.get('step')!=400"))
for name in ('export_identity','identities','metadata_closure'):
 a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name);b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.dump(a)==ast.dump(b),name
J.write(D/'IDENTITY_CHECKS.json',dict(status='PASS',functions=['export_identity','identities','metadata_closure'],allowed_change='Artifact milestone comparison uses exact sealed spec step; step400 branch remains available.'))
folders=[L/'work/build21/proofs/final_focused',L/'work/build21/proofs/edges',L/'work/build21/proofs/producer_edges',L/'work/build22/proofs/new_tests',D/'proofs/tests23/proofs/unit',D/'proofs/tests23b/unit',D/'proofs/capacity/final']
hits={name:set() for name in changed};evidence=[]
for folder in folders:
 if not (folder/'source_hashes.json').exists():continue
 hashes=J.load(folder/'source_hashes.json');records=J.load(folder/'hits.json');evidence.append(str(folder.relative_to(L)))
 for name in changed:
  if hashes.get(name)==files[name]:hits[name].update(records.get(name,[]))
coverage={n:dict(statements=v['changed_statements'],hit=sorted(set(v['changed_statements'])&hits[n]),uncovered=sorted(set(v['changed_statements'])-hits[n])) for n,v in changed.items()}
J.write(D/'COVERAGE.json',dict(files=coverage,total=sum(len(x['statements']) for x in coverage.values()),covered=sum(len(x['hit']) for x in coverage.values()),evidence=evidence))
print(digest(files),len(changed),'files changed')
