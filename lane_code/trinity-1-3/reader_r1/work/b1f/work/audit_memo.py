from pathlib import Path
import ast,collections,difflib,hashlib,json,sys,tarfile
W=Path.cwd();O=W/'out';B=W.parent/'b1p/out'
h=lambda b:hashlib.sha256(b).hexdigest()
with tarfile.open(B/'0.tgz') as t:a={m.name:t.extractfile(m).read() for m in t}
with tarfile.open(O/'0.tgz') as t:b={m.name:t.extractfile(m).read() for m in t}
changed=[n for n in sorted(a.keys()|b.keys()) if a.get(n)!=b.get(n)]
allowed={'9.json','b/e2e_reader/perception_memo.py','b/e2e_reader/real.py','b/e2e_reader/stage1.py','b/e2e_reader/parity.py','h1eval/perception.py','h1eval/h10/perception_own.py','h1eval/h10/launch.py','orchard_h10/prepare.py','orchard_h10/runner.py'}
assert set(changed)==allowed,changed
(O/'FILE_SHA256_DIFF.tsv').write_text('file\tbefore_sha256\tafter_sha256\tstatus\n'+''.join(f"{n}\t{h(a[n]) if n in a else '-'}\t{h(b[n])}\t{'changed' if n in a else 'added'}\n" for n in changed))
(O/'PATCH.diff').write_text(''.join(''.join(difflib.unified_diff(a.get(n,b'').decode().splitlines(True),b[n].decode().splitlines(True),fromfile='a/'+n if n in a else '/dev/null',tofile='b/'+n)) for n in changed))
def fn(blob,name):return next(n for n in ast.walk(ast.parse(blob)) if isinstance(n,ast.FunctionDef) and n.name==name)
checks=[]
for name in ('name_key','sam3_detect','features','propose','select','proposal_diagnostics'):
 assert ast.dump(fn(a['b/e2e_reader/stage1.py'],name))==ast.dump(fn(b['b/e2e_reader/stage1.py'],name)),name
 checks.append(name+' AST identical')
old=fn(a['b/e2e_reader/real.py'],'__call__');new=fn(b['b/e2e_reader/real.py'],'_fresh');new.name='__call__'
assert ast.dump(old)==ast.dump(new);checks.append('G3T fresh call AST identical')
for n in ('b/e2e_reader/grounding.py','b/e2e_reader/servers.py','b/e2e_reader/generate.py','b/e2e_reader/callhook.py','h1eval/scorers.py','h1eval/statistics.py','h1eval/h10/parity_adapter.py'):
 assert a[n]==b[n];checks.append(n+' bytes identical')
for prefix in ('tree/','b/heads/','b/parity_kit/','h1eval/reader_core/','items/','rows/'):
 assert all(a[n]==b[n] for n in a if n.startswith(prefix));checks.append(prefix+' all bytes identical')
(O/'DELTA_AUDIT.json').write_text(json.dumps(dict(base_sha256=h((B/'0.tgz').read_bytes()),payload_sha256=h((O/'0.tgz').read_bytes()),changed=changed,unchanged=sum(a.get(n)==v for n,v in b.items()),checks=checks),indent=2)+'\n')
sys.path.insert(0,str(W.parent/'b1/in/eat1'));import scan
findings=[]
for label,root in [('before',O/'baseline'),('after',O/'src')]:
 rows,suppressed=scan.scan([root/n for n in changed if n.endswith('.py') and (root/n).exists()],root=root)
 (O/f'EAT1_{label}.json').write_text(json.dumps(dict(findings=rows,suppressed=suppressed),indent=2)+'\n');findings.append(rows)
key=lambda r:(r['rel'],r['function'],r['rule'],r['detail'])
a0,b0=[collections.Counter(key(r) for r in rows if r['clause'] in ('A3','A4')) for rows in findings]
added=list((b0-a0).elements())
(O/'EAT1_DELTA.json').write_text(json.dumps(dict(before=sum(a0.values()),after=sum(b0.values()),added=added),indent=2)+'\n')
print(json.dumps(dict(changed=changed,unchanged=sum(a.get(n)==v for n,v in b.items()),A3_A4_added=added),indent=2))
