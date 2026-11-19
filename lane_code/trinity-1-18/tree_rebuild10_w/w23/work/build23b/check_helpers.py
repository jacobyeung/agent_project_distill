from pathlib import Path
import ast,json
L=Path(__file__).resolve().parents[2];D=L/'work/build23b'
for name in ('finish.py','package.py','capacity_final.py'):ast.parse((D/name).read_text(),filename=name)
counts=[]
B=L/'work/build21'
for g in ('final_focused','edges','producer_edges','b23b_resolver','b23b_kit','b23b_naming21c','b23b_naming21d','b23b_scanner'):
 v=json.loads((B/'proofs'/g/'TESTS.json').read_text());assert v['successful'];counts.append(v['tests'])
for p in (L/'work/build23/TESTS.json',L/'work/build23/RESOLVER_TESTS.json',D/'TESTS.json'):
 v=json.loads(p.read_text());assert v['successful'];counts.append(v['tests'])
print(json.dumps(dict(tests=sum(counts),inherited=sum(counts[:-1]),new=counts[-1])))
