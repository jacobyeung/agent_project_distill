from pathlib import Path
import ast,difflib,hashlib,json,sys,tarfile,datetime
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e';A=L/'attic/build21e'
sys.path[:0]=[str(B),str(L/'work/tree_r1')];import joblib as J
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
coverage={};changes=[];diff=[]
for name in ('joblib.py','kit.py','jobtest.py'):
    old=(A/name).read_text();new=(B/name).read_text();changed=set();hits=set();evidence=[]
    for tag,a,b,c,d in difflib.SequenceMatcher(None,old.splitlines(),new.splitlines(),autojunk=False).get_opcodes():
        if tag in ('replace','insert'):changed.update(range(c+1,d+1))
    for p in D.glob('TRACE_*.json'):
        value=J.load(p).get('work/build21/'+name)
        if value and value['sha256']==sha(B/name):hits.update(value['hits']);evidence.append(str(p.relative_to(L)))
    statements=[]
    for node in ast.walk(ast.parse(new)):
        if isinstance(node,ast.stmt) and node.lineno in changed:
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
            statements.append(dict(line=node.lineno,observed=node.lineno in hits,text=new.splitlines()[node.lineno-1]))
    if name!='jobtest.py':coverage[name]=dict(sha256=sha(B/name),observed=sum(x['observed'] for x in statements),total=len(statements),statements=statements,evidence=evidence)
    diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='base/'+name,tofile='build21e/'+name))
    changes.append(dict(path=str((B/name).relative_to(L)),before_sha256=sha(A/name),sha256=sha(B/name)))
J.write(D/'COVERAGE.json',dict(method='Standard-library tracing of changed AST statement heads; only exact current source hashes count.',files=coverage,
    observed=sum(x['observed'] for x in coverage.values()),total=sum(x['total'] for x in coverage.values())))
(D/'FIX.diff').write_text(''.join(diff))
J.write(D/'CHANGES.json',changes+[dict(path=str(p.relative_to(L)),new=True,sha256=sha(p)) for p in sorted(B.glob('*21e.py'))])
if '--coverage-only' in sys.argv:
    print(json.dumps({k:dict(observed=v['observed'],total=v['total'],uncovered=[s for s in v['statements'] if not s['observed']]) for k,v in coverage.items()},indent=2));raise SystemExit(0)
groups=('resolver21e','resolver_edges21e','final_focused','edges','producer_edges','kit21c','naming21c','extra21c','naming21d','coverage21d')
tests=[]
for group in groups:
    p=B/'proofs'/group/'TESTS.json';v=J.load(p);assert v['successful'],group
    tests.append(dict(name=group,tests=v['tests'],failures=len(v['failures']),errors=len(v['errors']),source=str(p.relative_to(L))))
J.write(D/'TESTS.json',tests)
from naming21 import scan_decoded
scan=scan_decoded(B/'kits/q');J.write(D/'SCAN.json',scan)
with tarfile.open(L/'out/tree_rebuild_b21c_6f5e6cc2.tar','r:gz') as t:before=json.load(t.extractfile('work/build21/UPLOADS.json'))
after=J.load(B/'UPLOADS.json');old={x['opaque_name']:x for x in before['files']};new={x['opaque_name']:x for x in after['files']}
delta=[]
for name in sorted(set(old)|set(new)):
    a=old.get(name);b=new.get(name)
    if a is None or b is None or (a['sha256'],a['bytes'])!=(b['sha256'],b['bytes']):
        delta.append(dict(name=name,before={k:a[k] for k in ('sha256','bytes')} if a else None,after={k:b[k] for k in ('sha256','bytes')} if b else None))
J.write(D/'UPLOAD_DIFF.json',dict(baseline='out/tree_rebuild_b21c_6f5e6cc2.tar:work/build21/UPLOADS.json',
    before_bytes=before['total_bytes'],after_bytes=after['total_bytes'],before_files=len(old),after_files=len(new),changed=delta))
start=J.load(D/'START.json');kit=B/'kits/q';files={str(p.relative_to(kit)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in kit.rglob('*') if p.is_file()}
J.write(D/'KIT_CHECK.json',dict(before=start['kit_seal'],after=J.seal(kit),files=len(files),
    changed=[n for n in sorted(set(files)|set(start['kit_files'])) if files.get(n)!=start['kit_files'].get(n)],
    tree_unchanged=J.load(L/'out/TREE_SEAL.json')==start['tree']))
(B/'STATUS.md').write_text('Build 21e: the resolver handles JSONL data and authenticates P runtime/kit identities. GO remains false.\n\n'
    'Real metadata replay: work/build21e/REPLAY.json. Tests, coverage, final scan and upload changes: work/build21e/.\n'
    'The sealed tree and staging paths are unchanged. No capacity restaging is required by the build condition.\n'
    'Delivery: work/build21e/DELIVERY.json. Report: out/BUILD21E_REPORT.md.\n')
print(json.dumps(dict(tests=tests,coverage=J.load(D/'COVERAGE.json')['observed'],scan=scan['status'],changed_uploads=[x['name'] for x in delta]),indent=2))
