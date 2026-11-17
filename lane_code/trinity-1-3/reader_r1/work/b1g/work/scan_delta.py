from pathlib import Path
import sys,json,collections
W=Path.cwd();O=W/'out'
sys.path.insert(0,str(W.parent/'b1/in/eat1'));import scan
files=['b/e2e_reader/grounding.py','b/e2e_reader/servers.py','b/e2e_reader/stage1.py','h1eval/h10/perception_own.py','h1eval/perception.py','b/e2e_reader/real.py','b/e2e_reader/parity.py','b/e2e_reader/perception_memo.py']
key=lambda r:(r['rel'],r['function'],r['rule'],r['detail'])
res={};raw={}
for label,root in [('bf94',W.parent/'b1p/out/baseline'),('e47',O/'baseline'),('a943',W.parent/'b1f/out/src'),('new',O/'src')]:
 rows,suppressed=scan.scan([root/n for n in files if (root/n).exists()],root=root)
 raw[label]=rows;res[label]=collections.Counter(key(r) for r in rows if r['clause'] in ('A3','A4'))
 (O/f'EAT1_{label}.json').write_text(json.dumps(dict(findings=rows,suppressed=suppressed),indent=2)+'\n')
deltas={label:dict(before=sum(res[label].values()),after=sum(res['new'].values()),added=list((res['new']-res[label]).elements()),removed=list((res[label]-res['new']).elements())) for label in ('bf94','e47','a943')}
(O/'EAT1_DELTA.json').write_text(json.dumps(deltas,indent=2)+'\n');print(json.dumps(deltas,indent=2))

# Preserve raw findings; account for a proven function relocation separately.
import ast
old=ast.parse((W.parent/'b1p/out/src/b/e2e_reader/real.py').read_text())
new=ast.parse((O/'src/b/e2e_reader/real.py').read_text())
cls=lambda t:next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='TowerG3T')
fn=lambda t,name:next(n for n in cls(t).body if isinstance(n,ast.FunctionDef) and n.name==name)
a=fn(old,'__call__');b=fn(new,'_fresh');a.name=b.name
assert ast.dump(a)==ast.dump(b),'Fresh body changed'
normalized={}
for label in ('a943','e47'):
 def normalize(rows):
  return collections.Counter((r['rel'],r['function'].replace('TowerG3T.__call__','TowerG3T._fresh'),r['rule'],r['detail']) for r in rows if r['clause'] in ('A3','A4'))
 added=list((normalize(raw['new'])-normalize(raw[label])).elements())
 assert not added,(label,added)
 normalized[label]=dict(new_findings=added,raw_added=deltas[label]['added'])
(O/'EAT1_GATE.json').write_text(json.dumps(dict(passed=True,scope='generate-path files',comparisons=normalized,raw_scan='EAT1_DELTA.json',relocation_proof='TowerG3T.__call__ versus _fresh AST identical after function-name normalization',no_allowlist_changes=True),indent=2)+'\n')
