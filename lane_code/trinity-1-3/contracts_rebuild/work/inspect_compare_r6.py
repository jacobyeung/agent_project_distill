from pathlib import Path
import json,collections
L=Path(__file__).resolve().parents[1];d=json.loads((L/'work/row_families_r6/comparison.json').read_text())
print(collections.Counter(x['path'] for x in d['defects']))
for r in d['families']:
 for s in r['samples']:
  bad=[x for x in s['differences'] if x['contract_change'] is None]
  if bad:
   print(r['family'],s['variant'],json.dumps(bad[:6])[:4000]);break
