from pathlib import Path
import ast,difflib,hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';T=L/'work/tree_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
observed={};evidence=[]
for p in (B/'proofs').rglob('hits.json'):
 if any('before' in n or n=='mutations' for n in p.relative_to(B/'proofs').parts):continue
 h=p.with_name('source_hashes.json')
 if not h.exists():continue
 hashes=json.loads(h.read_text());hits=json.loads(p.read_text())
 for name,lines in hits.items():
  for root in (T,B):
   path=root/name
   if path.is_file() and hashes.get(name)==sha(path):observed.setdefault(str(path),set()).update(map(int,lines))
 evidence.append(str(p.relative_to(L)))
names=set(json.loads((B/'ENV_CHANGES.json').read_text()))
if (B/'V2H_CHANGES.json').exists():names.update(json.loads((B/'V2H_CHANGES.json').read_text()))
names.update(('student_pilot/r1_coverage.py','student_pilot/job_env.py','launch_r1/production_proof.py','student_pilot/r2_openers.py'))
records=[];patch=[]
def collect(p,old):
 new=p.read_text();before=old.splitlines();after=new.splitlines();changed=set()
 for tag,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag in ('replace','insert'):changed.update(range(c+1,d+1))
 patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='build20/'+p.name,tofile=str(p.relative_to(L))))
 rows=[]
 for node in ast.walk(ast.parse(new)):
  if not isinstance(node,ast.stmt) or node.lineno not in changed:continue
  if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
  rows.append(dict(file=str(p.relative_to(L)),line=node.lineno,text=after[node.lineno-1],sha256=sha(p),observed=node.lineno in observed.get(str(p),set())))
 return rows
for name in sorted(names):
 p=T/name
 if not p.exists():continue
 base=B/'base'/name
 if not base.exists():base=B/'base'/p.name
 records.extend(collect(p,base.read_text() if base.exists() else ''))
kit=[]
for name in ('joblib.py','kit.py','naming21.py'):
 p=B/name;base=B/'base'/name
 kit.extend(collect(p,base.read_text() if base.exists() else ''))
value=dict(method='Changed AST statement heads against saved build-20 bytes. Only current SHA-256 and matching compiled-code fingerprints count.',
 total=len(records),observed=sum(r['observed'] for r in records),statements=records,
 kit=dict(total=len(kit),observed=sum(r['observed'] for r in kit),statements=kit),proofs=evidence)
(B/'DELTA_COVERAGE.json').write_text(json.dumps(value,indent=2));(L/'out/TREE.diff').write_text(''.join(patch))
print(json.dumps(dict(tree=(value['observed'],value['total']),kit=(value['kit']['observed'],value['kit']['total']))))
print(json.dumps([r for r in records if not r['observed']],indent=2))
