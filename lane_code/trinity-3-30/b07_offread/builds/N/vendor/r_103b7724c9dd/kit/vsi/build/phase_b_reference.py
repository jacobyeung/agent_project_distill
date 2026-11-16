"""Reduce accepted journals and reconstruct receipts against their accepted hashes."""
import hashlib
import json
from pathlib import Path
import sys
K=Path(__file__).resolve().parents[1]
P=K.parent/'pull/x27/res/e193/direct/main'
sys.path[:0]=[str(K/'reader/out'),str(K/'reader/evaluator')]
import direct,media
vendor,_=direct.modules();origin=vendor.R3
_,_,_,captures=origin.payload(K/'reader/work/vendor/r3')
expected=json.loads((K/'parity/ACCEPTED20.json').read_text());ids=[r['example_id'] for r in expected]
accepted={}
for arm,name in [('ON16k','items_leg_m544_main.jsonl'),('B2048','budget_2048.jsonl'),('B4096','budget_4096.jsonl')]:
 rows={}
 with (P/'results/0'/name).open() as f:
  for line in f:
   r=json.loads(line)
   if r['example_id'] in ids:rows[r['example_id']]=r
 assert set(rows)==set(ids)
 accepted[arm]=rows
cfg=json.loads((P/'request.json').read_text());index=json.loads((P/'frames/0.json').read_text())
receipts={};need=set()
for id in ids:
 r=accepted['ON16k'][id];pin=index['items'][media.item_key(r,'duplicate')]
 rec=origin.receipt_template(r,cfg['cells'][0],captures[r['native']],media)
 rec['audit']={k:v for k,v in r['media'].items() if k!='frame_receipt'}
 raw=(json.dumps(rec,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 if hashlib.sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('Cannot reconstruct accepted receipt: '+id)
 receipts[id]=dict(pin=pin,receipt=rec)
 need.update(f['sha256'] for f in rec['frames'])
fields=['example_id','prompt_text','prompt_token_ids','prompt_tokens','token_ids','raw_generation','extracted_answer','score','status']
result=dict(job=169526,ids=ids,request={k:cfg[k] for k in ('cells','max_tokens','temperature','thinking','max_model_len','max_seqs','inflight','engine_version','gpus')},
 prompt_probes=json.loads((P/'results/0/p0_leg_m544_main.json').read_text())['checks'],
 frames_index_sha256=hashlib.sha256((P/'frames/0.json').read_bytes()).hexdigest(),
 receipts=receipts,need=sorted(need),arms={a:[{k:r[k] for k in fields if k in r} for id in ids for r in [rows[id]]] for a,rows in accepted.items()})
(K/'parity/DEV20.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
(K/'proof/pull.py').write_bytes((K.parent/'pull/x27c/r0/x/pull.py').read_bytes())
print(json.dumps(dict(items=len(ids),frames=len(need),receipt_pins_verified=len(receipts),bytes=(K/'parity/DEV20.json').stat().st_size)))
