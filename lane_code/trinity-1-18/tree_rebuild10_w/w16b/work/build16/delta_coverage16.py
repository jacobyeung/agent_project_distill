"""Count changed AST statement heads using authenticated standard-library line events."""
from pathlib import Path
import ast,difflib,hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build16';T=L/'work/tree_r1'
base=json.loads((B/'BASE15_SEAL.json').read_text())['files']
prior=L.parent/'w15/work/tree_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
observed={};sources=[]
for p in (B/'proofs').rglob('hits.json'):
    if set(p.relative_to(B/'proofs').parts)&{'mutations','frozen'}:continue
    h=p.with_name('source_hashes.json')
    if not h.exists():continue
    hashes=json.loads(h.read_text());hits=json.loads(p.read_text())
    for name,lines in hits.items():
        if (T/name).is_file() and hashes.get(name)==sha(T/name):
            if isinstance(lines,dict):lines=list(map(int,lines))
            observed.setdefault(name,set()).update(map(int,lines))
    sources.append(str(p.relative_to(L)))
rows=[]
for p in sorted(T.rglob('*.py')):
    name=str(p.relative_to(T))
    if not name.startswith(('student_pilot/','launch_r1/')) or base.get(name)==sha(p):continue
    old=[]
    if name in base:
        assert sha(prior/name)==base[name]
        old=(prior/name).read_text().splitlines()
    new=p.read_text().splitlines();changed=set()
    for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
        if tag in ('replace','insert'):changed.update(range(c+1,d+1))
    for node in ast.walk(ast.parse(p.read_text())):
        if not isinstance(node,ast.stmt) or node.lineno not in changed:continue
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
        rows.append(dict(file=name,line=node.lineno,text=new[node.lineno-1],sha256=sha(p),observed=node.lineno in observed.get(name,set())))
result=dict(method='AST statement heads on added/changed lines against the authenticated build-15 source. Only build-16 observations with exact current file SHA-256 and compiled-source fingerprints count; no inherited hits.',
    statements=rows,total=len(rows),observed=sum(r['observed'] for r in rows),sources=sources)
(B/'DELTA_COVERAGE.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:result[k] for k in ('total','observed')}))
print(json.dumps([r for r in rows if not r['observed']],indent=2))
