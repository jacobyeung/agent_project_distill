from pathlib import Path
from collections import Counter,defaultdict
import ast,difflib,hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=L/'work/tree_r1';prior=L.parent/'w9f/work/tree_r1'
total=json.loads((B/'CHANGED_COVERAGE.json').read_text());observed=defaultdict(set)
for source in total['coverage_sources']:
    root=L/source['source'];hits=json.loads((root/'hits.json').read_text());hashes=json.loads((root/'source_hashes.json').read_text())
    for file in source['accepted_files']:
        if hashlib.sha256((T/file).read_bytes()).hexdigest()==hashes[file]:observed[file].update(hits[file])
classes={(r['file'],r['line']):r['classification'] for r in total['statements']}
records=[]
for item in json.loads((B/'SOURCE_PRESERVATION.json').read_text())['changes']:
    name=item['file'];p=T/name
    if not name.endswith('.py') or name.startswith('tests/'):continue
    before=(prior/name).read_text().splitlines() if (prior/name).exists() else []
    after=p.read_text().splitlines();changed=set()
    for tag,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if tag!='equal':changed.update(range(c+1,d+1))
    for node in ast.walk(ast.parse('\n'.join(after))):
        if not isinstance(node,ast.stmt) or (isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str)):continue
        nested=[x.lineno for field in ('body','orelse','finalbody') for x in getattr(node,field,[]) if isinstance(x,ast.stmt)]
        end=max(node.lineno,min(nested)-1) if nested else node.end_lineno
        if changed.intersection(range(node.lineno,end+1)):
            hit=node.lineno in observed[name]
            records.append(dict(file=name,line=node.lineno,executed=hit,
                classification='observed' if hit else classes.get((name,node.lineno),'CPU-reachable unresolved'),text=after[node.lineno-1]))
byfile={}
for r in records:byfile.setdefault(r['file'],Counter())[r['classification']]+=1
value=dict(method='Incremental build-10 statement heads versus the authenticated build-9fix source; same exact-file and compiled-code observation receipts as the base comparison.',
    classes=dict(Counter(r['classification'] for r in records)),by_file=byfile,statements=records)
(B/'INCREMENTAL_COVERAGE.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value['classes']))
