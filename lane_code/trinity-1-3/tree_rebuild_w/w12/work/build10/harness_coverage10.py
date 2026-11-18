from pathlib import Path
from collections import Counter
import ast,difflib,hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=B/'eat1';base=L.parent/'work/design/eat1_v7/eat1'
hits={};sources=[]
for folder in ('g8_contract','g8_available','adapter_manifest'):
    p=L/'work/build12/proofs'/folder/'COVERAGE.json'
    if not p.exists():continue
    sources.append(str(p.relative_to(L)))
    for name,r in json.loads(p.read_text()).items():
        file=Path(name)
        if file.is_relative_to(T) and file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest()==r['sha256']:
            hits.setdefault(str(file.relative_to(T)),set()).update(r['lines'])
rows=[]
for file in sorted(T.rglob('*.py')):
    name=str(file.relative_to(T));old=base/name
    before=old.read_text().splitlines() if old.exists() else [];after=file.read_text().splitlines();changed=set()
    for tag,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if tag!='equal':changed.update(range(c+1,d+1))
    for node in ast.walk(ast.parse('\n'.join(after))):
        if not isinstance(node,ast.stmt) or (isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str)):continue
        nested=[v.lineno for field in ('body','orelse','finalbody') for v in getattr(node,field,[]) if isinstance(v,ast.stmt)]
        end=max(node.lineno,min(nested)-1) if nested else node.end_lineno
        if not changed.intersection(range(node.lineno,end+1)):continue
        rows.append(dict(file=name,line=node.lineno,executed=node.lineno in hits.get(name,set()),
            kind='test' if name.startswith('tests/') else 'harness',text=after[node.lineno-1]))
value=dict(method='Standard-library sys.monitoring line observations, exact source-file SHA matched; no inferred execution. Harness observations do not use the production compiled-code fingerprint filter.',sources=sources,
    classes=dict(Counter(('observed' if r['executed'] else 'unobserved')+' '+r['kind'] for r in rows)),statements=rows,
    blocked_test='eat1.tests.test_eat1.StraceSource.test_strace_sees_the_planted_table: PTRACE_TRACEME denied; original failure retained at proofs/g8/test.log')
(B/'HARNESS_COVERAGE.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value['classes']))
