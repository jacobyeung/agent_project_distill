"""Keep response examples within the shared per-family retention bound."""
import collections,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
p=B/'proofs/responses/INVENTORY.json';value=json.loads(p.read_text())
examples=value['examples'] if isinstance(value,dict) else value
counts=collections.Counter();retained=[]
for entry in examples:
 stem=Path(entry['source']).stem
 family='absolute_distance' if 'abs_distance' in stem else stem
 if counts[family]<200:
  retained.append(entry);counts[family]+=1
out=dict(patterns=value.get('patterns',len(examples)) if isinstance(value,dict) else len(examples),
         examples=retained,retained_per_family=dict(counts),limit_per_family=200)
p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(retained_per_family=dict(counts))))
