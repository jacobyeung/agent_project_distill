from pathlib import Path
import ast,difflib,hashlib,json,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build21';C=L/'work/build21c';A=L/'attic/build21c'
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
observed={};sources=[]
for p in C.glob('TRACE_*.json'):
    record=json.loads(p.read_text());sources.append(str(p.relative_to(L)))
    for name,lines in record['hits'].items():
        if record['sha256'][name]==sha(B/name):observed.setdefault(name,set()).update(lines)
records=[];changes=[];diff=[]
if not (A/'jobtest.py').exists():
    with tarfile.open(L/'out/tree_rebuild_b21_b262e7a7.tar','r:gz') as archive:
        (A/'jobtest.py').write_bytes(archive.extractfile('work/build21/jobtest.py').read())
for name in ('joblib.py','naming21.py','kit.py','test21.py','jobtest.py'):
    old=(A/name).read_text();new=(B/name).read_text();before=old.splitlines();after=new.splitlines();changed=set()
    plus=minus=0
    for tag,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if tag in ('replace','insert'):changed.update(range(c+1,d+1));plus+=d-c
        if tag in ('replace','delete'):minus+=b-a
    changes.append(dict(path=str((B/name).relative_to(L)),added_lines=plus,removed_lines=minus,sha256=sha(B/name)))
    diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='build21/'+name,tofile='build21c/'+name))
    if name in ('test21.py','jobtest.py'):continue
    for node in ast.walk(ast.parse(new)):
        if isinstance(node,ast.stmt) and node.lineno in changed:
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
            records.append(dict(file=name,line=node.lineno,observed=node.lineno in observed.get(name,set()),text=after[node.lineno-1]))
write(C/'COVERAGE.json',dict(method='Standard-library line tracing; changed AST statement heads against saved build-21 files; only exact current file hashes count.',
    total=len(records),observed=sum(x['observed'] for x in records),statements=records,evidence=sources))
for p in sorted(B.glob('*21c.py')):
    if p.name in ('inspect21c.py','maps21c.py','start21c.py'):continue
    changes.append(dict(path=str(p.relative_to(L)),new=True,sha256=sha(p)))
write(C/'CHANGES.json',changes);(C/'FIX.diff').write_text(''.join(diff))
checks=[]
for group in ('final_focused','edges','producer_edges','kit21c','naming21c','extra21c'):
    p=B/'proofs'/group/'TESTS.json';v=json.loads(p.read_text())
    assert v['successful'],group
    checks.append(dict(name=group,tests=v['tests'],failures=len(v['failures']),errors=len(v['errors']),source=str(p.relative_to(L))))
write(C/'TESTS.json',checks)
uploads=json.loads((B/'UPLOADS.json').read_text());deps=json.loads((C/'DEPENDENCIES.json').read_text())
text=(A/'OPERATOR.md').read_text()
start=text.index('The decoded executable scanner');end=text.index('\n\n',start)
text=text[:start]+('The scanner checks every decoded operational map key and value, including `k/p.json` and its `p_files` inventory, '
    'nested staging payload paths, shell arguments, Python path literals and result archive member names. '
    'The job checks dynamic export and snapshot member names before writing them, and checks each authenticated directory map before staging it. '
    'Sealed source inventories and input-data schema fields retain their authenticated identities. '
    'The exact scanner inventory and runtime-only map pins are in `../build21c/SCAN.json`.')+text[end:]
start=text.index('\nUpload total:');text=text[:start]
text+=f'''\nThe exclusion payload stages as `k/3119aa4a.json`. Its SHA-256 remains
`3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970`.
The authenticated `p_sources` map reads the same bytes from N's `u/<sha256>` upload.
Configuration pins and hash-keyed catalogs use the pinned opaque map. P's original files remain unchanged.

Upload total: {uploads['total_bytes']} bytes in {len(uploads['files'])} files (source: `UPLOADS.json`).

The focused test fixture closure would add {deps['complete_additional_bytes']} bytes.
The delivery includes {deps['bytes']} bytes of smaller fixture inputs; the remaining prerequisites,
their hashes and paths are listed in `../build21c/DEPENDENCIES.json` under `omissions`.
The full focused suite therefore requires those listed inputs after unpacking.
No checkpoint, database or frame set is bundled for test replay.
The source tree remains sealed as `{json.loads((L/'out/TREE_SEAL.json').read_text())['tree_sha256']}`.

To replay the focused suites once the listed prerequisites are available, use the supplied environment
and run `nice -n 10 bash work/build21/run.sh work/build21/focused.py` from the delivery root.
The test helpers and the small baseline source/inputs are included. The original path identities in
authenticated records remain pinned; `B21C_PORTABLE=1` redirects bundled prerequisite reads by the
explicit dependency map without changing their bytes.
'''
(B/'OPERATOR.md').write_text(text)
print(json.dumps(dict(tests=checks,coverage=[sum(x['observed'] for x in records),len(records)],fixture_bytes=deps['bytes']),indent=2))
