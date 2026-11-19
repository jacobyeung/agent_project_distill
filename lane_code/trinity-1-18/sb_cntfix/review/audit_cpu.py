"""Read-only CPU audit; writes derived evidence with input SHA256s inside this workspace."""
import collections, gzip, hashlib, importlib.util, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
inputs={}
def read(p, gz=False):
 p=Path(p); raw=p.read_bytes(); inputs[str(p)]=hashlib.sha256(raw).hexdigest()
 return json.loads(gzip.decompress(raw) if gz else raw)
def pin(p):
 p=Path(p); h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 inputs[str(p)]=h.hexdigest()
 return h.hexdigest()
pin(__file__)
sp=ROOT/'kit/files/score_count_pricing.py'; pin(sp)
spec=importlib.util.spec_from_file_location('S',sp); S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
meta=read(ROOT/'kit/work/K1_LIFT_META.json'); keep={c['capture'] for c in meta['captures']}
rows=[]; allrows=[]; teacher_hash_bad=[]
for p in sorted((ROOT/'k1/labels_k1').glob('*.labels.json.gz')):
 lab=read(p,True)
 tp=ROOT/'k1/teacher_k1_full/teacher_k1'/p.name[:-len('.labels.json.gz')]/'teacher.json.gz'
 if lab['canonical'] in keep:
  h=pin(tp)
  if lab['teacher_sha256']!=h: teacher_hash_bad.append(lab['canonical'])
 for name, role in lab['roles'].items():
  if role!='gt':continue
  fs=[lab['frames'][str(k)].get(name,{}) for k in range(32)]
  visible=set().union(*(set(f.get('gt_visible',[])) for f in fs))
  if not visible:continue
  oracle={q['inst'] for f in fs for q in f.get('proposals',[]) if q.get('inst_name')==name and (q.get('iou') or 0)>=0.25 and q.get('inst') is not None}
  r=dict(capture=lab['canonical'],name=name,split=lab['k1_split'],truth=len(visible),oracle=len(oracle),gt_max=max(len(f.get('gt_visible',[])) for f in fs))
  allrows.append(r)
  if lab['canonical'] in keep:rows.append(r)
big=[r for r in rows if r['truth']>=5]; largeall=[r for r in allrows if r['truth']>=5]
summary={}
for label,rr in [('K1_overlap',rows),('K1_overlap_large',big),('K1_all_large',largeall)]:
 summary[label]=dict(pairs=len(rr),captures=len({r['capture'] for r in rr}),splits=dict(collections.Counter(r['split'] for r in rr)),constant6=100*np.mean([S.mra(6,r['truth']) for r in rr]),identity_iou25=100*np.mean([S.mra(r['oracle'],r['truth']) for r in rr]),gt_max=100*np.mean([S.mra(r['gt_max'],r['truth']) for r in rr]))
summary['label_teacher_sha_mismatches']=teacher_hash_bad
itemsfile=ROOT/'kit/files/COUNT_ITEMS_535.jsonl'; pin(itemsfile)
items=[json.loads(s) for s in itemsfile.read_text().splitlines()]
mismatch=[];n=0
for x in items:
 for k,d in x['direct'].items():
  n+=1; score=S.mra(d['pred'],x['truth'])
  if abs(score-d['score'])>1e-10:mismatch.append(dict(id=x['id'],arm=k,pred=d['pred'],truth=x['truth'],computed=score,stored=d['score']))
summary['stored_metric_check']=dict(comparisons=n,mismatches=mismatch,official_source='MISSING: no pinned official scorer implementation in supplied kit')
summary['item_integrity']=dict(items=len(items),unique_ids=len({x['id'] for x in items}),sets=dict(collections.Counter(x['set'] for x in items)),empty_categories=[x['id'] for x in items if not x['categories']],large_sets=dict(collections.Counter(x['set'] for x in items if x['truth']>=5)))
summary['bars']={s:{k:100*np.mean([x['direct'][k]['score'] for x in items if x['set']==s and x['truth']>=5]) for k in ['S1_544','R1_200']} for s in ['R0-dev','dev-S1']}
summary['constants']={s:{str(c):100*np.mean([S.mra(c,x['truth']) for x in items if x['set']==s and x['truth']>=5]) for c in [5,6,7]} for s in ['R0-dev','dev-S1']}
summary['metric_boundary_example']={'pred':11,'truth':10,'kit_MRA':S.mra(11,10),'stored_MRA':0.9}
receiptpath=Path('/scratch/jjyeung/orch_n30/b05_owngrd/code/owngrd/vendor/SAM3_RECEIPT.json')
receipt=read(receiptpath); src=Path('/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src')
summary['source_receipt']={p:pin(src/p)==sha for p,sha in receipt['source_files'].items()}
done=[read(p) for p in sorted((ROOT/'k1/teacher_k1_full/teacher_k1').glob('*/DONE.json'))]
secs=sum(d['seconds'] for d in done); names=sum(d['names'] for d in done)
summary['GPU_estimate']=dict(captures=len(done),names=names,seconds=secs,seconds_per_prompt=secs/names,R0DEV_names=464,R0DEV_projected_GPU_hours=464*secs/names/3600,note='Recorded capture time covers encode/detect, including lazy model loading, but excludes frame loading; this is an extrapolation, not a new GPU measurement.')
summary['pilot_inputs_missing_from_kit']=[str(ROOT/'kit/work'/f) for f in ['K1_PAIRS.json.gz','K1_LIFT.npz','K1_NMS.npz','K1_LMERGE.json','K1_LEARN_EST.json'] if not (ROOT/'kit/work'/f).exists()]
# Independently recompute the supplied summary's constant and identity oracle; never select a new rule.
print(json.dumps(summary,indent=2))
summary['inputs_sha256']=inputs
(ROOT/'out/CPU_AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n')
