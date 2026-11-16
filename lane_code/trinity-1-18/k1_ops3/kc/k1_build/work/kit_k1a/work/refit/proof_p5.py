import sys,json,copy
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent.parent)]
import train,prooflib
def proof():
 inv=json.loads((prooflib.LANE/'out/CAPTURES.json').read_text());pilot=inv['pilot']
 rows=[];pairs=[]
 for split in ('train','heldout'):
  captures=[c for c in pilot if c['split']==split][:4]
  for c in captures:
   for i in range(8):
    rows.append(dict(kind='candidate',scene=c['canonical'],object_id=c['canonical']+'::chair'+str(i//2),candidate_id=str(i),name='chair',y=i%2,
       features={k:float((j+1)*(i+1)%13) for j,k in enumerate(train.L.FEATS['portable_np'])}))
    pairs.append(dict(scene=c['canonical'],object_id=c['canonical']+'::chair'+str(i//2),a=str(i),b=str(i+1),y=i%2,ya=1,yb=1,
       f={k:float((j+3)*(i+1)%17) for j,k in enumerate(train.L.PFEATS)}))
 train.audit_features(rows);train.audit_features(pairs,True)
 mutations=[]
 for pair,key,data in [(False,'features',rows),(True,'f',pairs)]:
  bad=copy.deepcopy(data);bad[0][key]['gt_iou']=.99
  try:train.audit_features(bad,pair)
  except ValueError:mutations.append(key)
  else:raise AssertionError('Label-derived feature passed')
 folder=prooflib.LANE/'work/refit/p5_fixture';folder.mkdir(exist_ok=True)
 for name,data in [('candidates.jsonl',rows),('pairs.jsonl',pairs)]:
  (folder/name).write_text(''.join(json.dumps(r)+'\n' for r in data))
 import tempfile
 # train() requires an exclusive child output, keeping every proof attempt.
 parent=Path(tempfile.mkdtemp(prefix='fit_',dir=folder))
 result=train.train(folder/'candidates.jsonl',folder/'pairs.jsonl',prooflib.LANE/'out/CAPTURES.json',parent/'result',fixture=True)
 assert set(result['train_rooms']).isdisjoint(result['heldout_rooms'])
 sys.path.insert(0,str(train.gate.ROOT/'rs_tree/work/tree_r1'))
 from student_pilot.candidate_policy import Policy,predict
 native_path=parent/'result/NATIVE_POLICY.json'
 policy=Policy(dict(name='routed_default_v1',weights=dict(path=str(native_path),sha256=train.gate.sha(native_path))),'object_abs_distance')
 portable=json.loads((parent/'result/MODELS.json').read_text())
 native_delta=max(abs(predict(policy.weights['accept'],r['features'])-train.probability(portable['accept'],[r])[0]) for r in rows)
 assert native_delta<=1e-12,native_delta
 bad=copy.deepcopy(rows);bad[0]['scene']='scannet/scene0011_00'
 try:train.split_rows(bad,pilot)
 except ValueError:mutations.append('benchmark_scene')
 else:raise AssertionError('Excluded fit scene passed')
 return dict(versions=train.versions(),fixture_only=True,real_candidate_metrics_unmeasured=True,native_export_max_difference=native_delta,mutations_refused=mutations,fit_receipt=str(parent/'result/FIT_RECEIPT.json'),thresholds=result['thresholds'],thresholds_source=result['thresholds_source'])
if __name__=='__main__':raise SystemExit(not prooflib.run('P5',proof))
