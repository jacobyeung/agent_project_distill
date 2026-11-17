from pathlib import Path
import ast,collections,difflib,hashlib,json,sys,tarfile
W=Path.cwd();O=W/'out';h=lambda b:hashlib.sha256(b).hexdigest()
def inventory(path):
 with tarfile.open(path) as t:return {m.name:t.extractfile(m).read() for m in t if m.isfile()}
b=inventory(O/'0.tgz');bases={'bf94a7976a7e9':W.parent/'b1p/in/repin/out/0.tgz','c91bb8ec884e9':W.parent/'b1m/out/0.tgz'}
reports={}
for label,path in bases.items():
 a=inventory(path);names=sorted(a.keys()|b.keys());changed=[n for n in names if a.get(n)!=b.get(n)]
 tsv='file\tbefore_sha256\tafter_sha256\tstatus\n'+''.join(f"{n}\t{h(a[n]) if n in a else '-'}\t{h(b[n]) if n in b else '-'}\t{'identical' if a.get(n)==b.get(n) else 'changed' if n in a and n in b else 'added' if n in b else 'removed'}\n" for n in names)
 (O/f'FILE_SHA256_DIFF_vs_{label}.tsv').write_text(tsv)
 diff=''.join(''.join(difflib.unified_diff(a.get(n,b'').decode().splitlines(True),b.get(n,b'').decode().splitlines(True),fromfile='a/'+n if n in a else '/dev/null',tofile='b/'+n if n in b else '/dev/null')) for n in changed)
 # Include operator-kit changes separately from sealed-payload members.
 oldkit=W.parent/('b1m/out' if label=='c91bb8ec884e9' else 'b1p/out')
 for n in ('tower_sequence.py','tower_bootstrap.py','tower_pair.py','unpack_return.py','node_check.py','build_operator.py'):
  diff+=''.join(difflib.unified_diff((oldkit/n).read_text().splitlines(True),(O/n).read_text().splitlines(True),fromfile='a/operator/'+n,tofile='b/operator/'+n))
 (O/f'PATCH_vs_{label}.diff').write_text(diff)
 if label=='bf94a7976a7e9':(O/'PATCH.diff').write_text(diff)
 reports[label]=dict(base_sha256=h(path.read_bytes()),payload_sha256=h((O/'0.tgz').read_bytes()),changed=changed,unchanged=len(names)-len(changed))
a=inventory(bases['c91bb8ec884e9'])
protected=['b/e2e_reader/stage1.py','b/e2e_reader/grounding.py','b/e2e_reader/servers.py','h1eval/h10/perception_own.py','b/e2e_reader/generate.py','b/e2e_reader/callhook.py','h1eval/scorers.py','h1eval/statistics.py']
for n in protected:assert a[n]==b[n],n
for prefix in ('tree/','b/heads/','b/parity_kit/','h1eval/reader_core/','items/','rows/'):
 assert all(a[n]==b[n] for n in a if n.startswith(prefix)),prefix
old=ast.parse(a['b/e2e_reader/real.py']);new=ast.parse(b['b/e2e_reader/real.py'])
fn=lambda tree,name:next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
assert ast.dump(fn(old,'_fresh'))==ast.dump(fn(new,'_fresh'))
old=ast.parse(a['h1eval/h10/parity_adapter.py']);new=ast.parse(b['h1eval/h10/parity_adapter.py']);assert ast.dump(fn(old,'make_capped_real'))==ast.dump(fn(new,'make_capped_real'))
reports['protected_sha256']={n:h(b[n]) for n in protected};reports['checks']=['protected files byte-identical to c91','frozen G3T fresh AST identical','call-cap factory AST identical','tree, heads, parity kit, reader_core, items, rows byte-identical']
(O/'DELTA_AUDIT.json').write_text(json.dumps(reports,indent=2)+'\n')
# W3 scan method: all changed Python files, retaining operator findings in raw output.
sys.path.insert(0,str(W.parent/'b1/in/eat1'));import scan
files=set(reports['c91bb8ec884e9']['changed'])|{'b/e2e_reader/stage1.py','b/e2e_reader/grounding.py','b/e2e_reader/servers.py','h1eval/h10/perception_own.py'}
res={}
for label,root in [('before',W.parent/'b1m/out/src'),('after',O/'src')]:
 rows,suppressed=scan.scan([root/n for n in sorted(files) if n.endswith('.py') and (root/n).exists()],root=root)
 (O/f'EAT1_W3_{label}.json').write_text(json.dumps(dict(findings=rows,suppressed=suppressed),indent=2)+'\n')
 res[label]=collections.Counter((r['rel'],r['function'],r['rule'],r['detail']) for r in rows if r['clause'] in ('A3','A4'))
raw=dict(before=sum(res['before'].values()),after=sum(res['after'].values()),added=list((res['after']-res['before']).elements()),removed=list((res['before']-res['after']).elements()))
(O/'EAT1_W3_DELTA.json').write_text(json.dumps(raw,indent=2)+'\n')
reader=lambda r:r[0].startswith('b/e2e_reader/') or r[0] in ('h1eval/perception.py','h1eval/h10/perception_own.py')
assert not [r for r in raw['added'] if reader(r)]
print(json.dumps(dict(payload=reports,raw_scan=raw),indent=2))
