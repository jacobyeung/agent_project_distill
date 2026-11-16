"""Changed executable statement lines against the original base; never infer hits."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2]
tree=L/'work/tree_r1';base=L/'work/base/tree_b01ce449'
hits={};sources=[]
for directory in map(Path,sys.argv[1:]):
    if not (directory/'source_hashes.json').exists():
        continue
    hashes=json.loads((directory/'source_hashes.json').read_text())
    observed=json.loads((directory/'hits.json').read_text())
    accepted=[]
    for name,lines in observed.items():
        p=tree/name
        if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==hashes.get(name):
            hits.setdefault(name,set()).update(lines);accepted.append(name)
    sources.append(dict(path=str(directory),accepted_files=len(accepted)))
rows=[]
for p in sorted(tree.rglob('*.py')):
    name=str(p.relative_to(tree))
    if name.startswith('tests/'):
        continue
    old=(base/name).read_text().splitlines() if (base/name).exists() else []
    new=p.read_text().splitlines()
    changed=set()
    for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
        if tag!='equal':changed.update(range(c+1,d+1))
    if not changed:continue
    code=ast.parse('\n'.join(new))
    statements={n.lineno for n in ast.walk(code) if isinstance(n,ast.stmt) and not (
        isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))}
    for line in sorted(statements & changed):
        reached=line in hits.get(name,set())
        rows.append(dict(file=name,line=line,source=str(p),executed=reached,
            classification='observed' if reached else 'CPU-reachable, unresolved',text=new[line-1].strip()))
record=dict(baseline=str(base),tree=str(tree),coverage_sources=sources,changed_statements=len(rows),
    executed=sum(r['executed'] for r in rows),unexecuted=sum(not r['executed'] for r in rows),
    method='AST statement start lines changed from base; current-file hash matched standard-library monitoring evidence only. No inferred or historical hits.',
    limitation='Unexecuted statements conservatively remain CPU-reachable unresolved; this does not satisfy zero CPU gaps.',statements=rows)
(L/'work/build4/CHANGED_COVERAGE.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ('statements','coverage_sources')}))
