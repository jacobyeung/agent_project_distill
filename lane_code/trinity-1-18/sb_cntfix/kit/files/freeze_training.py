"""Select from the complete per-frame rule family using K1 TRAINING captures only."""
import collections,gzip,json,sys
from pathlib import Path
import numpy as np
import count_guard as G
from official_vsi_mra import official_mra
import score_count_pricing as S
R=Path(__file__).resolve().parents[2]
def main():
 meta=R/'kit/work/K1_LIFT_META.json';caps=[c['capture'] for c in G.read(meta)['captures'] if c['split']=='train']
 inputs={str(meta):G.sha(meta),str(Path(__file__)):G.sha(__file__),str(G.HERE/'official_vsi_mra.py'):G.sha(G.HERE/'official_vsi_mra.py'),str(G.HERE/'score_count_pricing.py'):G.sha(G.HERE/'score_count_pricing.py')}
 rules=[dict(nms=n,kind=k,joint=t,iou=.5,contain=.8,stride=2) for n in (False,True) for k in ('max','second') for t in (.35,.5,.6,.7,.8,.9)]
 rows=[]
 for ci,cap in enumerate(caps):
  key=cap.replace('/','__');lp=R/'k1/labels_k1'/(key+'.labels.json.gz');tp=R/'k1/teacher_k1_full/teacher_k1'/key/'teacher.json.gz'
  with gzip.open(lp,'rt') as f:lab=json.load(f)
  if lab['k1_split']!='train' or lab['canonical']!=cap:raise ValueError('training authorization mismatch')
  inputs[str(lp)]=G.sha(lp);inputs[str(tp)]=G.sha(tp)
  if lab['teacher_sha256']!=inputs[str(tp)]:raise ValueError('K1 label/teacher hash mismatch')
  with gzip.open(tp,'rt') as f:teacher=json.load(f)
  for name,role in lab['roles'].items():
   if role!='gt':continue
   vis=set().union(*(set(lab['frames'][str(k)].get(name,{}).get('gt_visible',[])) for k in range(32)))
   if not vis:continue
   # Decode masks once per frame; compute each threshold's raw/NMS counts once.
   counts={}
   for nms in (False,True):
    for th in (.35,.5,.6,.7,.8,.9):counts[nms,th]=[]
   for k in range(32):
    ins=teacher['frames'][str(k)]['phrases'][name]['instances']
    decoded=[(i['joint_score'],S.rle_decode(i['mask'])[::2,::2]) for i in sorted(ins,key=lambda x:-x['joint_score'])]
    for th in (.35,.5,.6,.7,.8,.9):
     selected=[m for s,m in decoded if s>=th];kept=[]
     for m in selected:
      a=int(m.sum())
      if not a:continue
      if any((lambda z,b:z and (z/float(a+b-z)>.5 or z/float(min(a,b))>.8))(int((m&q).sum()),b) for q,b in kept):continue
      kept.append((m,a))
     counts[False,th].append(len(selected));counts[True,th].append(len(kept))
   est=[]
   for rule in rules:
    v=sorted(counts[rule['nms'],rule['joint']],reverse=True);est.append(v[0] if rule['kind']=='max' else (v[1] if v[1]>0 else v[0]))
   rows.append(dict(capture=cap,category=name,truth=len(vis),estimates=est))
  if ci%25==0:print('training captures',ci+1,'/',len(caps),flush=True)
 big=[r for r in rows if r['truth']>=5]
 means=[100*sum(official_mra(r['estimates'][i],r['truth']) for r in big)/len(big) for i in range(len(rules))]
 best=max(range(len(rules)),key=lambda i:means[i])
 constants={str(c):100*sum(official_mra(c,r['truth']) for r in big)/len(big) for c in (5,6,7)}
 const=int(max(constants,key=constants.get))
 by=collections.defaultdict(list)
 for r in big:by[r['capture']].append(100*(official_mra(r['estimates'][best],r['truth'])-official_mra(const,r['truth'])))
 ci=S.boot(by);decision='ACCEPT_FOR_COMPARISON' if means[best]>constants[str(const)] and ci[0]>0 else 'REJECT_ON_TRAINING'
 frozen=dict(schema='count-training-freeze-v2',training_split='train',training_captures=caps,training_pairs=len(rows),training_large_pairs=len(big),candidate_family=rules,candidate_train_MRA=means,rule=rules[best],best_const=const,constant_train_MRA=constants,selected_train_MRA=means[best],selected_minus_constant_CI=list(ci),training_decision=decision,
  decision=dict(primary_set='R0-dev',diagnostic_only_set='dev-S1',comparator='S1_544',accept='training ACCEPT_FOR_COMPARISON and N > direct and N >= frozen constant and paired room-bootstrap lower bound > 0',gain_threshold=0,CI_lower_threshold=0,bootstrap_draws=10000,bootstrap_seed=20261119,large_truth_min=5,pooled_decision=False),
  response=dict(enabled=decision=='ACCEPT_FOR_COMPARISON',format='per-category per-frame counts; selected count and frame',row_filter='K1 train only; truth >= 5; exact selected count equals truth',dev_changes_allowed=False),
  inherited_teacher_contract=G.CONTRACT,constraint_notes='IoU .5, containment .8, stride 2 are fixed candidate-family constraints evaluated on training; raw alternatives are included. Ties use listed order. No held-out or dev statistic enters selection.',inputs_sha256=inputs)
 G.write(G.HERE/'FROZEN_CONFIG.json',frozen)
 G.write(R/'out/K1_TRAIN_SELECTION.json',dict(rows=rows,inputs_sha256=inputs))
 print(json.dumps({k:frozen[k] for k in ('training_pairs','training_large_pairs','rule','best_const','selected_train_MRA','constant_train_MRA','selected_minus_constant_CI','training_decision')},indent=2))
if __name__=='__main__':main()
