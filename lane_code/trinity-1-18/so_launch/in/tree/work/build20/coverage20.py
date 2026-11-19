from pathlib import Path
import ast,difflib,hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build20';T=L/'work/tree_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
observed={};sources=[]
for p in (B/'proofs').rglob('hits.json'):
    if set(p.relative_to(B/'proofs').parts)&{'mutations','frozen','before'}:continue
    h=p.with_name('source_hashes.json')
    if not h.exists():continue
    hashes=json.loads(h.read_text());hits=json.loads(p.read_text())
    for name,lines in hits.items():
        root=B if p.parent.name=='job' else T
        path=root/name
        if path.is_file() and hashes.get(name)==sha(path):observed.setdefault(str(path),set()).update(map(int,lines))
    sources.append(str(p.relative_to(L)))
rows=[]
for name in ('r1_handover.py','r1_training.py','r1_components.py','r2_contract.py','carrier_c1_run.py'):
    old=(B/'base'/name).read_text().splitlines();p=T/'student_pilot'/name;new=p.read_text().splitlines();changed=set()
    for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
        if tag in ('replace','insert'):changed.update(range(c+1,d+1))
    for node in ast.walk(ast.parse(p.read_text())):
        if not isinstance(node,ast.stmt) or node.lineno not in changed:continue
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
        rows.append(dict(file=str(p.relative_to(L)),line=node.lineno,text=new[node.lineno-1],sha256=sha(p),observed=node.lineno in observed.get(str(p),set())))
job=[];p=B/'joblib.py'
for node in ast.walk(ast.parse(p.read_text())):
    if not isinstance(node,ast.stmt):continue
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
    job.append(dict(line=node.lineno,observed=node.lineno in observed.get(str(p),set())))
value=dict(method='Changed AST statement heads against saved build-19 bytes; only current SHA-256 and compiled-source fingerprint observations count.',
    total=len(rows),observed=sum(r['observed'] for r in rows),statements=rows,sources=sources,
    job_library=dict(file='work/build20/joblib.py',sha256=sha(p),total=len(job),observed=sum(r['observed'] for r in job),statements=job))
(B/'DELTA_COVERAGE.json').write_text(json.dumps(value,indent=2))
print(json.dumps({k:value[k] for k in ('total','observed')}));print('job',value['job_library']['observed'],len(job))
print(json.dumps([r for r in rows if not r['observed']],indent=2))
