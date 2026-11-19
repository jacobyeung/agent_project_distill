from pathlib import Path
import ast,difflib,hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21d';A=L/'attic/build21d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
old=(A/'naming21.py').read_text();new=(B/'naming21.py').read_text();changed=set()
for tag,a,b,c,d in difflib.SequenceMatcher(None,old.splitlines(),new.splitlines(),autojunk=False).get_opcodes():
    if tag in ('replace','insert'):changed.update(range(c+1,d+1))
hits=set();evidence=[]
for p in D.glob('TRACE_*.json'):
    value=read(p)
    if value['sha256']==sha(B/'naming21.py'):hits.update(value['hits']);evidence.append(str(p.relative_to(L)))
statements=[]
for node in ast.walk(ast.parse(new)):
    if isinstance(node,ast.stmt) and node.lineno in changed:
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
        statements.append(dict(line=node.lineno,observed=node.lineno in hits,text=new.splitlines()[node.lineno-1]))
write(D/'COVERAGE.json',dict(method='Standard-library tracing of changed AST statement heads; only exact current source hashes count.',
    sha256=sha(B/'naming21.py'),observed=sum(x['observed'] for x in statements),total=len(statements),statements=statements,evidence=evidence))
(D/'FIX.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='build21c/naming21.py',tofile='build21d/naming21.py')))
assert sha(B/'joblib.py')==sha(A/'joblib.py')
changes=[dict(path=str((B/'naming21.py').relative_to(L)),before_sha256=sha(A/'naming21.py'),sha256=sha(B/'naming21.py'))]
changes.extend(dict(path=str(p.relative_to(L)),new=True,sha256=sha(p)) for p in sorted(B.glob('*21d.py')))
write(D/'CHANGES.json',changes)
if '--coverage-only' in sys.argv:
    print(json.dumps(dict(observed=sum(x['observed'] for x in statements),total=len(statements),
        uncovered=[x for x in statements if not x['observed']]),indent=2))
    raise SystemExit(0)
groups=('final_focused','edges','producer_edges','kit21c','naming21c','extra21c','naming21d','coverage21d')
tests=[]
for group in groups:
    p=B/'proofs'/group/'TESTS.json';value=read(p);assert value['successful'],group
    tests.append(dict(name=group,tests=value['tests'],failures=len(value['failures']),errors=len(value['errors']),source=str(p.relative_to(L))))
write(D/'TESTS.json',tests)
text=(A/'OPERATOR.md').read_text()
start=text.index('The scanner checks');end=text.index('\n\n',start)
text=text[:start]+('The scanner checks every decoded key and string value, including nested payloads, '
    'and every literal contribution to Python and shell environment assignments and passed environment maps. '
    'Exact authenticated content exceptions, their reasons and use restrictions are listed in `../build21d/ALLOWLIST.json`; '
    'no nested payload is exempt. The scan and unchanged kit proof are in `../build21d/SCAN.json` and `../build21d/KIT_CHECK.json`. '
    'The job checks dynamic staging and archive names. Runtime-supplied arguments and inherited environment values '
    'are not evaluated by the static scanner.')+text[end:]
(B/'OPERATOR.md').write_text(text)
(B/'STATUS.md').write_text('Build 21d: scanner checks and required regressions pass; GO remains false.\n\n'
    'The kit and sealed tree are unchanged. Evidence: work/build21d/SCAN.json, KIT_CHECK.json, TESTS.json and COVERAGE.json.\n'
    'Delivery: work/build21d/DELIVERY.json. Report: out/BUILD21D_REPORT.md.\n')
print(json.dumps(dict(tests=tests,coverage=[sum(x['observed'] for x in statements),len(statements)]),indent=2))
