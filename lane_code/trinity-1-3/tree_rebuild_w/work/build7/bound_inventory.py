import collections,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];p=L/'work/build7/proofs/responses/INVENTORY.json'
rows=json.loads(p.read_text());seen=collections.Counter();bounded=[]
for r in rows:
 if seen[r['source']]<200:bounded.append(r);seen[r['source']]+=1
p.write_text(json.dumps(dict(patterns=len(rows),examples=bounded),indent=2)+'\n')
v=json.loads((L/'work/build7/proofs/rows/RESULTS.json').read_text())
counts=collections.Counter()
for r in v['families']:counts.update(r['counts'])
print(json.dumps(dict(counts=counts,missing_frame_dimensions='RGB and dimensions absent from most bound row slices')))
old=json.loads((L/'work/build7/proofs/audit/BUILD6_REGRESSIONS.json').read_text())
print(json.dumps([r['test'] for r in old]))
