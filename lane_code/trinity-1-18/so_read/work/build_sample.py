from collections import Counter
import hashlib
import json
from pathlib import Path

L=Path('/scratch/jjyeung/orch_n30/so_read')
A=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4')
source=A/'src/items/devs1_routed.json';m=json.loads(source.read_text())
types=['object_abs_distance','camera_displacement','camera_rotation','camera_movement_direction','room_size_estimation']
selected=[]
for kind in types:
    pool=[r for r in m['items'] if r['question_type']==kind]
    counts=Counter(r.get('native',r['room_key']) for r in pool)
    ordered=sorted(pool,key=lambda r:(-counts[r.get('native',r['room_key'])],r.get('native',r['room_key']),r['id']))
    selected.extend(ordered[:10])
selected.sort(key=lambda r:r['id'])
encoded=json.dumps(selected,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
sample={k:m[k] for k in ('schema','name','status','development_only')}
sample.update(items=selected,item_set_sha256=hashlib.sha256(encoded).hexdigest(),count=50,
              per_type=dict(Counter(r['question_type'] for r in selected)),
              source={'path':'items/devs1_routed.json','sha256':hashlib.sha256(source.read_bytes()).hexdigest()},
              r0_check={**m['r0_check'],'checked':50})
out=L/'out/kit_parity50';out.mkdir(parents=True,exist_ok=True)
(out/'sample50.json').write_text(json.dumps(sample,indent=2,sort_keys=True)+'\n')
receipt=dict(schema='fixed-parity-sample-v1',source=str(source),source_sha256=sample['source']['sha256'],
             sample_sha256=hashlib.sha256((out/'sample50.json').read_bytes()).hexdigest(),
             rule='Ten per type; sort by descending native-capture frequency, native key, then ID. No scores used.',
             purpose='Stress scene reuse; not a representative speed benchmark.',ids=[r['id'] for r in selected],
             per_type=sample['per_type'],native_captures=len({r.get('native',r['room_key']) for r in selected}))
(out/'SAMPLE_IDENTITY.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='ids'},indent=2))
