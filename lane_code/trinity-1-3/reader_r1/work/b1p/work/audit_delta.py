from pathlib import Path
import ast,json,hashlib,tarfile,difflib,sys,collections
W=Path.cwd();O=W/'out';base=O/'baseline';new=O/'src'
def h(b):return hashlib.sha256(b).hexdigest()
with tarfile.open(W/'in/repin/out/0.tgz') as t:a={m.name:t.extractfile(m).read() for m in t}
with tarfile.open(O/'0.tgz') as t:b={m.name:t.extractfile(m).read() for m in t}
changed=[n for n in sorted(a.keys()|b.keys()) if a.get(n)!=b.get(n)]
allowed=['9.json','b/e2e_reader/grounding.py','b/e2e_reader/servers.py','b/e2e_reader/stage1.py','b/e2e_reader/real.py','b/e2e_reader/parity.py','h1eval/h10/depth_snapshot.py','h1eval/h10/launch.py','h1eval/h10/perception_own.py','h1eval/perception.py','orchard_h10/runner.py','orchard_h10/prepare.py']
assert set(changed)==set(allowed),changed
(O/'FILE_SHA256_DIFF.tsv').write_text('file\tbefore_sha256\tafter_sha256\tstatus\n'+''.join(f"{n}\t{h(a[n]) if n in a else '-'}\t{h(b[n]) if n in b else '-'}\t{'changed' if n in a else 'added'}\n" for n in changed))
(O/'PATCH.diff').write_text(''.join(''.join(difflib.unified_diff(a.get(n,b'').decode().splitlines(True),b.get(n,b'').decode().splitlines(True),fromfile='a/'+n if n in a else '/dev/null',tofile='b/'+n)) for n in changed))
# Strip observational statements, then compare the default decision AST exactly.
def fn(root,file,name):return next(n for n in ast.walk(ast.parse((root/file).read_text())) if isinstance(n,ast.FunctionDef) and n.name==name)
checks=[]
def same(label,old,new):
 assert ast.dump(old)==ast.dump(new),label
 checks.append(label)
f='b/e2e_reader/stage1.py'
old=fn(base,f,'features');cur=fn(new,f,'features')
cur.body=[n for n in cur.body if not (isinstance(n,ast.Assign) and ast.unparse(n.targets[0]).startswith('self.diagnostics['))]
class Rename(ast.NodeTransformer):
 def visit_Name(self,n):
  if n.id=='lift_outcomes':n.id='_'
  return n
same('candidate production after removing diagnostic assignment',old,Rename().visit(cur))
old=fn(base,f,'select');cur=fn(new,f,'select')
# The default uses exactly the old head slots and argmax; candidate-only branches do not execute.
cur.body=[n for n in cur.body if isinstance(n,ast.Assign) and ast.unparse(n.targets[0]) in ('slots','k','choice')]
choice=cur.body.pop();cur.body.append(ast.Return(value=choice.value))
same('null_argmax slot evaluation, tie rule, and null mapping',old,cur)
for name in ('sam3_detect','name_key','propose'):same(name,fn(base,f,name),fn(new,f,name))
f='b/e2e_reader/grounding.py';same('socket decision path',fn(base,f,'__call__'),fn(new,f,'__call__'))
for name in ('lift_plain','lift_bestspread','min_area_box','ground_session'):same(name,fn(base,f,name),fn(new,f,name))
f='b/e2e_reader/servers.py';old=fn(base,f,'session_call');cur=fn(new,f,'session_call')
i=next(i for i,n in enumerate(cur.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='info')
cur.body=cur.body[:i]+[ast.Return(value=ast.Tuple(elts=[ast.Name(id='text',ctx=ast.Load()),cur.body[i].value],ctx=ast.Load()))]
same('printed server response and existing audit',old,cur)
# Exact bytes establish all untouched scorers, caps, producers, formatter and dependencies.
assert a['h1eval/h10/parity_adapter.py']==b['h1eval/h10/parity_adapter.py']
for prefix in ('tree/','b/heads/','b/parity_kit/','h1eval/reader_core/','items/','rows/'):
 assert all(a[n]==b[n] for n in a if n.startswith(prefix)),prefix
result=dict(before=h((W/'in/repin/out/0.tgz').read_bytes()),after=h((O/'0.tgz').read_bytes()),changed=changed,
 unchanged=sum(a.get(n)==v for n,v in b.items()),ast_checks=checks,
 protected='Admission, restore, call caps, scorers, statistics, items, tree, heads, reader_core and inventories are byte-identical to bf94.')
(O/'DELTA_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
# Same EAT-1 scanner and allowlist as B1; compare semantic findings, ignoring shifted line numbers.
sys.path.insert(0,'/scratch/jjyeung/orch_n30/reader_r1/work/b1/in/eat1');import scan
scope=['b/e2e_reader/grounding.py','b/e2e_reader/servers.py','b/e2e_reader/stage1.py','h1eval/h10/perception_own.py','h1eval/perception.py','b/e2e_reader/real.py','b/e2e_reader/parity.py']
findings=[]
for label,root in [('before',base),('after',new)]:
 rows,suppressed=scan.scan([root/n for n in changed if n.endswith('.py') and (root/n).exists()],root=root)
 (O/f'EAT1_{label}.json').write_text(json.dumps(dict(findings=rows,suppressed=suppressed),indent=2)+'\n');findings.append(rows)
key=lambda r:(r['rel'],r['function'],r['rule'],r['detail'])
a0,b0=[collections.Counter(key(r) for r in rows if r['rel'] in scope) for rows in findings]
added=list((b0-a0).elements());gate=dict(scope=scope,before_findings=sum(a0.values()),after_findings=sum(b0.values()),new_findings=added,passed=not added,whole_reader_EAT1_pass=False,no_allowlist_changes=True,
 exclusions='Post-generation depth snapshot, launcher, preparation and runner are orchestration/output paths; raw scans retain their findings.')
(O/'EAT1_GATE.json').write_text(json.dumps(gate,indent=2)+'\n');assert not added,added
print(json.dumps(result));print(json.dumps(gate))
