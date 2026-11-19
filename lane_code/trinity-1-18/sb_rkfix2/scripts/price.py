"""The only R0-dev pricing entry point; one exclusive, persistent decision registration."""
from common import *
from gates import run_code_hashes
import selection
BAR=67.75510204081633
DECISION='PASS iff MRA >= bar and paired 95% lower bound > 0; NEAR iff MRA >= bar; otherwise FAIL'

def run():
 root=W/'out/room_pricing'
 for name in ('ROOM_PRED.jsonl','PRICING_TABLE.json','DECISION_REGISTRATION.json'):
  if (root/name).exists():raise RuntimeError('one R0-dev look already registered or consumed: '+name)
 code=run_code_hashes();chosen=selection.load_selection(root,code);arm=chosen['arm']
 if (root/'ARM_DROPPED.json').exists():raise RuntimeError('selected arm dropped; no R0-dev look')
 manifest_path=W/'configs/R0DEV_ROOM_MANIFEST.json';manifest=read(manifest_path)
 ins={str(manifest_path):sha(manifest_path),str(root/'SELECTION.json'):sha(root/'SELECTION.json'),**code}
 direct=W/'evidence/direct_m200_room134.json'
 if sha(direct)!=BASE:raise ValueError('baseline changed')
 ins[str(direct)]=BASE
 for item in manifest['items']:
  p=root/'pred'/arm/item['scene']/'pred.npz';d=p.parent/'DONE.json'
  if not p.is_file() or not d.is_file():raise FileNotFoundError('MISSING '+str(p))
  rec=read(d);b=rec['binding'];expected=item['frame_indices'] if arm=='da3_f32' else item['union_indices']
  if sha(p)!=rec['pred_sha256'] or b['code_sha256']!=code or b['manifest_sha256']!=sha(manifest_path):raise ValueError('stale inference receipt')
  if b['frames']!=expected or b['item_slots']!=[expected.index(i) for i in item['frame_indices']] or b['arm']!=arm:raise ValueError('stale frame or arm binding')
  ins[str(p)]=sha(p);ins[str(d)]=sha(d)
 registration=dict(bar=BAR,arm=arm,rule='R0',decision=DECISION,code_sha256=digest(code),selection_sha256=sha(root/'SELECTION.json'),input_sha256=ins)
 # O_EXCL serializes scorers after completeness; conversion failures consume the look.
 with (root/'DECISION_REGISTRATION.json').open('x') as f:json.dump(registration,f,indent=2)
 from kernel import pipeline,input_code
 import score_room_pricing as scorer
 ins.update(input_code());ins[str(root/'DECISION_REGISTRATION.json')]=sha(root/'DECISION_REGISTRATION.json')
 rows=[]
 for item in manifest['items']:
  p=root/'pred'/arm/item['scene']/'pred.npz';d=p.parent/'DONE.json'
  result=pipeline(p,root/'geom'/arm/(item['scene']+'.npz'),'R0')
  rows.append(dict(id=item['id'],arm=arm+'+R0',**result,input_sha256={str(p):sha(p),str(d):sha(d),**code}))
 output=root/'ROOM_PRED.jsonl'
 with output.open('x') as f:f.write(''.join(json.dumps(r,allow_nan=False)+'\n' for r in rows))
 ins[str(output)]=sha(output)
 table=scorer.score(read(direct)['rows'],rows,arm+'+R0',5)
 if abs(table['decision']['bar']-BAR)>1e-10:raise ValueError('registered bar mismatch')
 table['interpretation']='PASS/FAIL evaluates this complete measurement pipeline against R0 mesh labels, not geometry quality alone. Sensor-depth label audit: proposed, unbuilt.'
 write(root/'PRICING_TABLE.json',table,ins);(root/'PRICING_TABLE.txt').write_text(scorer.render(table));print(scorer.render(table))
if __name__=='__main__':run()
