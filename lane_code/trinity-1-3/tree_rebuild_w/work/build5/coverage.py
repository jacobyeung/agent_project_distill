"""Current-file-hash matched changed-statement coverage; no inferred hits."""
import ast
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
tree=L/'work/tree_r1';base=L/'work/base/tree_b01ce449'
sources=[Path(p).resolve() for p in sys.argv[1:]]
if not sources:raise SystemExit('Supply current proof folders with compiled-source monitoring receipts')
hits={};accepted=[];excluded=[]
for output in sources:
    if not (output/'source_hashes.json').is_file() or not (output/'hits.json').is_file():continue
    result=json.loads((output/'results.json').read_text())
    if result.get('coverage_code_filter')!='compiled-source fingerprint':
        excluded.append(dict(source=str(output.relative_to(L)),reason='No compiled-source code fingerprint filter'))
        continue
    hashes=json.loads((output/'source_hashes.json').read_text())
    observed=json.loads((output/'hits.json').read_text())
    names=[]
    for name,lines in observed.items():
        path=tree/name
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==hashes.get(name):
            hits.setdefault(name,set()).update(lines);names.append(name)
    accepted.append(dict(source=str(output.relative_to(L)),accepted_files=names))
rows=[]
for p in sorted(tree.rglob('*.py')):
    name=str(p.relative_to(tree))
    if any(part in ('artifacts','.git','__pycache__') for part in p.relative_to(tree).parts):continue
    if name.startswith('tests/'):continue
    new=p.read_text().splitlines();prior=(base/name).read_text().splitlines() if (base/name).is_file() else []
    changed=set()
    for tag,a,b,c,d in difflib.SequenceMatcher(None,prior,new,autojunk=False).get_opcodes():
        if tag!='equal':changed.update(range(c+1,d+1))
    if not changed:continue
    parsed=ast.parse('\n'.join(new))
    funcs=[n for n in ast.walk(parsed) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    statements={n.lineno for n in ast.walk(parsed) if isinstance(n,ast.stmt) and not (
        isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))}
    for line in sorted(statements&changed):
        fn=next((n.name for n in sorted(funcs,key=lambda n:n.end_lineno-n.lineno) if n.lineno<=line<=n.end_lineno),'module')
        reached=line in hits.get(name,set())
        category='observed' if reached else 'CPU-reachable unresolved'
        reason=None
        if not reached:
            if name=='launch_r2/staging.py' and fn=='main':
                category='frame-host';reason='Missing pinned venv archive and bwrap executable on the frame host.'
            elif name=='launch_r2/entry.py' and fn=='main' and line>=59:
                category='frame-host';reason='Missing admitted full-store packet and actual host receipts; production launch additionally needs GPU authorization.'
            elif name=='launch_r2/worker.py' and fn=='main':
                category='GPU';reason='Missing authorized worker allocation, real pretrained export and distributed training process group.'
            elif name=='student_pilot/carrier_c1_run.py' and fn in ('train','load_model'):
                category='GPU' if fn=='train' else 'model-loader'
                reason=('Missing admitted real pretrained weights and distributed CUDA training allocation.'
                        if fn=='train' else 'Missing the pinned pretrained export weights, processor configuration and authenticated warm-start artifact.')
            elif name=='launch_r2/host.py' and fn=='execute_packet' and line in (252,266):
                category='frame-host';reason='Missing the real sealed pose-source bytes needed to pass packet validation before post-staging checks and the bound remote transport probe.'
            elif name=='launch_r2/host.py' and fn=='execute_packet' and (line==310 or 312<=line<=319):
                category='frame-host';reason='Missing frame-host node admission and the pinned step-544 init archive; the Trinity full-store guard must remain enabled.'
            elif name=='launch_r2/host.py' and fn=='execute_packet' and 331<=line<=333:
                category='frame-host';reason='Missing the full registered admitted reader population and final sampling receipt; a bounded local store cannot meet the registered repeat limits.'
            elif name=='launch_r2/host.py' and fn=='execute_packet' and (335<=line<=337 or 354<=line<=356):
                category='frame-host';reason='Missing real bank files, the staged step-544 vocabulary witness and complete native runtime outputs from the full host job.'
            elif name=='student_pilot/r2_materialize.py' and fn=='materialize' and line in (25,26,27,118,119):
                category='frame-host';reason='Missing an admitted frame host and its full frame population; the local full-store guard prevents this branch.'
            elif name=='student_pilot/r2_materialize.py' and fn=='materialize' and line==152:
                category='frame-host';reason='Missing a full admitted population meeting registered repeat limits; bounded local materialization must refuse that sampling receipt.'
        row=dict(file=name,line=line,function=fn,source=str(p.relative_to(L)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                 executed=reached,classification=category,text=new[line-1].strip())
        if reason:row['reason']=reason
        rows.append(row)
record=dict(method='AST changed statement starts relative to untouched base; stdlib monitoring filtered by compiled-source fingerprints and exact current-file hashes.',
    changed_statements=len(rows),executed=sum(r['executed'] for r in rows),classes=dict(Counter(r['classification'] for r in rows)),
    coverage_sources=accepted,excluded_sources=excluded,statements=rows)
(L/'work/build5/CHANGED_COVERAGE.json').write_text(json.dumps(record,indent=2)+'\n')
gaps={}
for row in rows:
    if row['classification']=='CPU-reachable unresolved':gaps.setdefault(row['file'],[]).append((row['line'],row['text']))
(L/'work/build5/GAPS.json').write_text(json.dumps(gaps,indent=2)+'\n')
print(json.dumps(dict(classes=record['classes'],cpu_gaps={k:len(v) for k,v in gaps.items()})))
