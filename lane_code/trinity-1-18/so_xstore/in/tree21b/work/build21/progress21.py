from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
r=json.loads((B/'proofs/receipts/RESULT.json').read_text())
print('receipts',len(r['receipts']),'prepared',len(r['prepared']),'children',len(r['children']))
for x in r['prepared']:print(x['preparation']['sha256'][:8],x['stream'],x['status'],x.get('error',''))
index=json.loads((B/'proofs/receipts/INDEX.json').read_text())
for h in ('d8d33340aabfe1e58d4bc81cd3b2c4919510c38c419ea9d81abe520844f6a1a9','3cb1ccf5af6e75eb1b5a28bd7bfacbaf0ab9f8485a0fb55866dcd86271d1352a'):print('order',h,index.get(h))
p=B/'proofs/capacity/RESULT.json'
if p.exists():
 v=json.loads(p.read_text());print('capacity last completed summary',v.get('refusal'),{k:x.get('status') for k,x in v['milestones'].items()})
e=json.loads((L/'work/build21/inputs/config.json').read_text())['extent_receipt']['path']
a=json.loads(Path(e).read_text())['audits'];print('extent audit type',type(a).__name__)
import hashlib
for path in (L.parent/'inputs/p_runtime').rglob('receipt.json'):
 raw=path.read_bytes();v=json.loads(raw);print('runtime',str(path),len(raw),hashlib.sha256(raw).hexdigest(),v.get('schema'))
 for name,entry in v.get('streams',{}).items():print(name,entry.get('receipt'))
