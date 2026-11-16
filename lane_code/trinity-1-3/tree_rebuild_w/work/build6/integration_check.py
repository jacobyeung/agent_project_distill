"""Recheck installed contract bytes and the preserved level-basis source."""
import ast,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6';T=L/'work/tree_r1'
rows=json.loads((B/'INTEGRATION.json').read_text())
for row in rows:
 actual=hashlib.sha256((T/row['file']).read_bytes()).hexdigest()
 assert actual==row['after'],row['file']
 if row['route']=='exact':assert actual==row['manifest_patched'],row['file']
levels=[]
for p in T.rglob('*.py'):
 if 'artifacts' in p.parts:continue
 text=p.read_text()
 if 'def level_basis(' not in text:continue
 old=L/'work/contracts_r6/tree_copy'/p.relative_to(T)
 def function(raw):
  node=next(n for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.FunctionDef) and n.name=='level_basis')
  return '\n'.join(raw.splitlines()[node.lineno-1:node.end_lineno])
 assert function(text)==function(old.read_text()),str(p)
 levels.append(str(p.relative_to(T)))
result=dict(files=len(rows),exact=sum(r['route']=='exact' for r in rows),merged=sum(r['route']=='merged' for r in rows),level_basis_byte_identical=levels)
(B/'INTEGRATION_CHECK.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
