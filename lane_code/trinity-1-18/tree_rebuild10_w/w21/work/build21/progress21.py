from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
r=json.loads((B/'proofs/receipts/RESULT.json').read_text())
print('receipts',len(r['receipts']),'prepared',len(r['prepared']),'children',len(r['children']))
for x in r['prepared']:print(x['preparation']['sha256'][:8],x['stream'],x['status'],x.get('error',''))
p=B/'proofs/capacity/RESULT.json'
if p.exists():
 v=json.loads(p.read_text());print('capacity last completed summary',v.get('refusal'),{k:x.get('status') for k,x in v['milestones'].items()})
e=json.loads((L/'work/build21/inputs/config.json').read_text())['extent_receipt']['path']
a=json.loads(Path(e).read_text())['audits'];print('extent audit type',type(a).__name__)
