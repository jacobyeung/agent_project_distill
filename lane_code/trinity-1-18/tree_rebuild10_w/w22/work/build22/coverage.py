"""Count changed statements only when the executing source hash matches delivery."""
from pathlib import Path
import ast,difflib,hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build22';T=L/'work/tree_r1'
changes=json.loads((D/'TREE_CHANGES.json').read_text());hits={};sources=[]
roots=[D/'proofs/new_tests',D/'proofs/census',D/'proofs/capacity']
roots += [L/'work/build21/proofs'/name for name in ('final_focused','edges','producer_edges','build22_scanner','build22_resolver','build22_kit','build22_naming21c','build22_naming21d')]
for root in roots:
    if not (root/'hits.json').is_file():continue
    found=json.loads((root/'hits.json').read_text());hashes=json.loads((root/'source_hashes.json').read_text());sources.append(str(root.relative_to(L)))
    for name,lines in found.items():
        if name in changes and hashes.get(name)==changes[name]['after']:hits.setdefault(name,set()).update(lines)
records={}
for name,change in changes.items():
    statements=set(change.get('changed_statements',[]));seen=hits.get(name,set())
    records[name]=dict(sha256=change['after'],covered=len(statements&seen),total=len(statements),missing=sorted(statements-seen))
p=L/'work/build21/environment21f.py';raw=p.read_text();old=(D/'before/environment21f.py').read_text();changed=set()
for tag,i,j,k,m in difflib.SequenceMatcher(a=old.splitlines(),b=raw.splitlines(),autojunk=False).get_opcodes():
    if tag!='equal':changed.update(range(k+1,m+1))
statements=changed&{n.lineno for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.stmt)}
scanner=json.loads((D/'proofs/new_tests/SCANNER_COVERAGE.json').read_text());seen=set(scanner['hits']);assert scanner['sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
records['build-scanner/environment21f.py']=dict(sha256=scanner['sha256'],covered=len(statements&seen),total=len(statements),missing=sorted(statements-seen))
result=dict(files=records,sources=sources,covered=sum(v['covered'] for v in records.values()),total=sum(v['total'] for v in records.values()))
(D/'COVERAGE.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['covered'],result['total']);print(json.dumps({k:(v['covered'],v['total'],v['missing']) for k,v in records.items()},indent=2))
