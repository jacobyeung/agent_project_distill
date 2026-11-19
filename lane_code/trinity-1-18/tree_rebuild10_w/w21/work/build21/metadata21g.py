from pathlib import Path
import ast,datetime,difflib,hashlib,json,sys,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g';A=L/'attic/build21g';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
groups=['scanner21g','resolver21g','kit21g','naming21cg','extra21cg','naming21dg','final_focused','edges','producer_edges']
assert all(x['returncode']==0 for x in J.load(D/'SUITES.json'))
assert len(J.load(D/'SUITES.json'))==7
tests=[]
for group in groups:
    p=B/'proofs'/group/'TESTS.json';v=J.load(p);assert v['successful'],group
    tests.append(dict(name=group,tests=v['tests'],failures=len(v['failures']),errors=len(v['errors']),source=str(p.relative_to(L))))
J.write(D/'TESTS.json',tests)
verification=J.load(B/'FINAL_KITS.json')
assert verification['kits']['q']['kit_sha256']==J.seal(K)
scan=verification['decoded_scan'];assert scan['status']=='PASS';J.write(D/'SCAN.json',scan)
baseline=L/'out/tree_rebuild_b21e_ac8fa8e3.tar'
with tarfile.open(baseline,'r:gz') as t:before=json.load(t.extractfile('work/build21/UPLOADS.json'))
assert before==J.load(A/'UPLOADS.json')
after=J.load(B/'UPLOADS.json');old={x['opaque_name']:x for x in before['files']};new={x['opaque_name']:x for x in after['files']}
delta=[]
for name in sorted(set(old)|set(new)):
    a=old.get(name);b=new.get(name)
    if a is None or b is None or (a['sha256'],a['bytes'])!=(b['sha256'],b['bytes']):
        delta.append(dict(name=name,before={k:a[k] for k in ('sha256','bytes')} if a else None,after={k:b[k] for k in ('sha256','bytes')} if b else None))
J.write(D/'UPLOAD_DIFF.json',dict(baseline='out/tree_rebuild_b21e_ac8fa8e3.tar:work/build21/UPLOADS.json',before_bytes=before['total_bytes'],after_bytes=after['total_bytes'],before_files=len(old),after_files=len(new),changed=delta))
assert {x['name'] for x in delta}=={'q/k/j.json','q/SHA256SUMS.txt','q/BUILD.json'}
start=J.load(D/'START.json');files={str(p.relative_to(K)):dict(bytes=p.stat().st_size,sha256=J.sha(p)) for p in K.rglob('*') if p.is_file()}
manifest=J.load(A/'PACKAGE_MANIFEST.json');tree_files=0
for name,value in manifest['files'].items():
    if name.startswith('work/tree_r1/'):
        p=L/name;assert p.stat().st_size==value['bytes'] and J.sha(p)==value['sha256'],name
        tree_files+=1
assert J.load(L/'out/TREE_SEAL.json')==start['tree']
spec=J.load(K/'k/p.json');assert J.sha(L.parent/'ext/pwrap/b/c.sh')==spec['p_files']['b/c.sh']
assert J.sha(B/'joblib.py')==J.sha(A/'joblib.py')
assert J.sha(K/'b/z.py')==J.sha(B/'joblib.py')
J.write(D/'INTEGRITY.json',dict(status='PASS',tree_files_verified=tree_files,tree_seal=start['tree']['tree_sha256'],
    p_wrapper_unchanged=True,joblib_unchanged=True,GO=False,kit_seal_before=start['kit_seal'],kit_seal_after=J.seal(K),
    kit_changed=[name for name in sorted(set(files)|set(start['kit_files'])) if files.get(name)!=start['kit_files'].get(name)]))
coverage={};diff=[]
for name in ('environment21f.py','naming21.py','kit.py','naming_test21f.py'):
    p=B/name;old_source=(A/name).read_text();source=p.read_text();changed=set();hits=set()
    for tag,i,j,a,b in difflib.SequenceMatcher(a=old_source.splitlines(),b=source.splitlines(),autojunk=False).get_opcodes():
        if tag!='equal':changed.update(range(a+1,b+1))
    for trace in D.glob('TRACE_*.json'):
        entry=J.load(trace).get(str(p.relative_to(L)))
        if entry and entry['sha256']==J.sha(p):hits.update(entry['hits'])
    statements={n.lineno for n in ast.walk(ast.parse(source)) if isinstance(n,ast.stmt)}
    coverage[name]=dict(sha256=J.sha(p),changed_statements=len(changed & statements),changed_covered=len(changed & statements & hits),
        missing=sorted((changed & statements)-hits),note='Generated shell executes in VIEW.json; the generator insertion is also checked against exact expected shell bytes.' if name=='kit.py' else '')
    diff.extend(difflib.unified_diff(old_source.splitlines(True),source.splitlines(True),fromfile='base/'+name,tofile='build21g/'+name))
J.write(D/'COVERAGE.json',coverage);(D/'FIX.diff').write_text(''.join(diff))
operator=(B/'OPERATOR.md').read_text()
a=operator.index('The scanner checks every decoded key');b=operator.index('\n\nThe result archive',a)
operator=operator[:a]+'''The scanner checks every decoded key/string value, all literal environment contributions, and unresolved environment operations. Only the whole unmodified host environment may be inherited through a spread or copy; every added key is checked. Runtime Python values require one of the five explicit path names in `environment21f.py`. Complex shell programs require their exact reviewed source hash and the literal-name runtime allowlist in `environment_shell21g.json`; any edit invalidates that proof. The authenticated content exceptions remain in `../build21d/ALLOWLIST.json`. Final scan and upload differences: `../build21g/SCAN.json` and `../build21g/UPLOAD_DIFF.json`.

The view mounts a private writable `/tmp`, restores the node-local job root at its original path, then applies the remaining binds and `/tmp/q_22c714e1` alias. It creates no pool mount point. AS, AL and P must already exist wherever their host ancestor is read-only; an absent top-level prefix can instead be created under the namespace root. Those earlier binds succeeded in job 173051. Their values and every ordered destination are in `../build21g/MOUNTS.json`. The CPU stand-in view passes; the production GPU/model/store proof remains required.''' + operator[b:]
import re
operator=re.sub(r'Upload total: \d+ bytes in \d+ files',f'Upload total: {after["total_bytes"]} bytes in {len(new)} files',operator)
(B/'OPERATOR.md').write_text(operator)
(B/'STATUS.md').write_text('Build 21g: the kit gives the namespace bind a private writable /tmp parent and restores the job root. GO remains false.\n\n'
    'Mount reproduction and CPU in-view evidence: work/build21g/VIEW.json, NATIVE_VIEW.json, ROOM_VIEW.json.\n'
    'The scanner accepts checked whole-environment inheritance and refuses the required mutations.\n'
    'Tests, coverage, final scan, seals and upload differences: work/build21g/. The sealed tree and P wrapper are unchanged.\n')
print(json.dumps(dict(tests=sum(x['tests'] for x in tests),scan=scan['status'],kit=J.seal(K),uploads=[x['name'] for x in delta]),indent=2))
