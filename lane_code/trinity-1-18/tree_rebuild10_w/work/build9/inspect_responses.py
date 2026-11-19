import collections,json,re
from pathlib import Path
L=Path(__file__).resolve().parents[2]
examples={};counts=collections.Counter()
for root in (L/'work/rows_slices/slices_final',L/'fixtures/rows/slices_v3'):
 for p in sorted(root.glob('*.jsonl')):
  for i,line in enumerate(p.open()):
   if i>=2000:break
   r=json.loads(line);text=r.get('target',r.get('suffix',''))
   for body in re.findall(r'<tool_response>(.*?)</tool_response>',text,re.S):
    key=re.sub(r'[-+]?\d+(?:\.\d+)?','#',body)
    counts[key]+=1
    examples.setdefault(key,dict(source=str(p.relative_to(L)),body=body))
result=[dict(**examples[k],count=counts[k]) for k in counts]
p=L/'work/build9/proofs/responses';p.mkdir(parents=True,exist_ok=True)
retained=collections.Counter()
bounded=[]
for r in result:
 if retained[r['source']]<200:bounded.append(r);retained[r['source']]+=1
(p/'INVENTORY.json').write_text(json.dumps(dict(patterns=len(result),examples=bounded),indent=2)+'\n')
for r in result[:25]:print(json.dumps(r))
print('patterns',len(result))
