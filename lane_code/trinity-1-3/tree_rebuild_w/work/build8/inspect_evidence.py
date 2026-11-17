import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2]
if sys.argv[1]=='regressions':
 p=L/'work/build8/proofs/regressions/results.json'
 if p.exists():
  v=json.loads(p.read_text());print({k:(len(v[k]) if isinstance(v[k],list) else v[k]) for k in ('tests','passed','failures','errors','complete')})
  for k in ('failures','errors'):
   for row in v[k]:print(k,row)
 p=p.with_name('BF16_PARITY.json')
 if p.exists():
  for c in json.loads(p.read_text())['cases']:
   print(c['case'],c['verdict'],[(k,v) for k,v in c['tensors'].items() if not v['pass']])
elif sys.argv[1]=='frames':
 for r in json.loads((L/'work/build7/proofs/audit/FRAME64_REMAINING_SITES.json').read_text()):print(r['file'],r['line'],r['text'])
elif sys.argv[1]=='failures':
 for row in json.loads((L/'work/build7/SUITE_COMPARISON.json').read_text())['failures']:
  if row.get('classification')!='pre-existing':print(row)
