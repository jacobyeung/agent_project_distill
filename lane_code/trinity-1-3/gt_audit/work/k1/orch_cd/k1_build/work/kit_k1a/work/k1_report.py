"""Pre-registered held-out-room K1 decision; no benchmark labels or tuning."""
import argparse,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
sys.path.insert(0,str(gate.ROOT/'o3_cache/work/kit/vendor_sam/vendor'))
from score_and_aggregate_orchard import official_mra
RULES=dict(schema='b6-k1-rules-v1',seed=17,trust_relative_tolerance=.15,min_trust_fallback_share=.40,
 min_mra_gain=.10,max_auc_drop=.02,max_top1_drop=.02,cue_auc_bar=.65,
 mra_thresholds=[.50,.55,.60,.65,.70,.75,.80,.85,.90,.95],
 constant_fit='maximize training absolute-distance MRA over all interval endpoints; choose smaller value on ties',
 cue_directions=dict(status=1,low_frames=-1,spread=1,missing_size=1,disagreement=1),
 thresholds_source='b6_design section 4.6; trace_ruling cue study; frozen scorer',
 thresholds_fit_population='none; constants preregistered before K1 outputs',
 train_statistics_population='K1 train physical rooms only')
def mra(pred,gt):
 return official_mra(None if pred is None else float(pred),float(gt),.5,.95,.05)
def constant(values):
 if not values or any(x<0 or not math.isfinite(x) for x in values):raise ValueError('Invalid training GT')
 # Sweep closed tolerance intervals: exact training optimum without a label-derived grid.
 events={}
 for g in values:
  for t in RULES['mra_thresholds']:
   lo=g*t;hi=g*(2-t);events.setdefault(lo,[0,0])[0]+=1;events.setdefault(hi,[0,0])[1]+=1
 score=best=-1;chosen=None;score=0
 for x,(start,end) in sorted(events.items()):
  score+=start
  if score>best:best=score;chosen=x
  score-=end
 return chosen
def auc(labels,scores):
 pairs=sorted(zip(scores,labels));n1=sum(labels);n0=len(labels)-n1
 if not n0 or not n1:return None
 rank_sum=0.;i=0
 while i<len(pairs):
  j=i+1
  while j<len(pairs) and pairs[j][0]==pairs[i][0]:j+=1
  rank_sum+=sum(y for _,y in pairs[i:j])*(i+j+1)/2;i=j
 return (rank_sum-n1*(n1+1)/2)/(n0*n1)
def report(rows,inventory,fit_receipt,expected_ids=None):
 if expected_ids is not None and (len(rows)!=len(expected_ids) or {r['id'] for r in rows}!=set(expected_ids)):raise ValueError('K1 outcomes do not cover the complete preregistered row denominator')
 membership={c['canonical']:c for c in inventory['pilot']};seen=set();train=[];test=[]
 for r in rows:
  if r['id'] in seen:raise ValueError('Duplicate K1 row')
  seen.add(r['id']);ds,cap=r['canonical'].split('/')
  if not gate.eligible(ds,cap) or r['canonical'] not in membership:raise ValueError('Non-K1 result')
  if r['type']!='object_abs_distance':continue
  (train if membership[r['canonical']]['split']=='train' else test).append(r)
 if not train or not test:raise ValueError('Need train and held-out distance rows')
 c=constant([r['gt_value'] for r in train]);answered=[r for r in test if r['pred'] is not None]
 share=sum(r['label'] in ('trust','fallback') for r in test)/len(test)
 mean=lambda xs:sum(xs)/len(xs) if xs else None
 program=mean([mra(r['pred'],r['gt_value']) for r in answered]);baseline=mean([mra(c,r['gt_value']) for r in answered])
 met=fit_receipt['metrics']['accept'];da=met['refit']['auc']-met['current']['auc'];dt=met['refit']['top1_accept_accuracy']-met['current']['top1_accept_accuracy']
 cues={}
 for name,direction in RULES['cue_directions'].items():
  subsets={}
  for subset,pop in [('all',test),('answered',answered)]:
   available=[r for r in pop if name in r.get('printed_cues',{})]
   labels=[int(r['pred'] is None or abs(r['pred']-r['gt_value'])>.15*abs(r['gt_value'])) for r in available]
   subsets[subset]=dict(n=len(available),auc=auc(labels,[direction*r['printed_cues'][name] for r in available]))
  cues[name]=subsets
 return dict(train_constant=c,heldout_items=len(test),answered_items=len(answered),trust_fallback_share=share,
  complete_row_denominator_checked=expected_ids is not None,
  available_training_targets=sum(r.get('training_target_available',False) for r in test),
  answered_mra=program,constant_mra=baseline,auc_delta=da,top1_delta=dt,printed_cues=cues,
  kill_rows=share<.4 or program is None or program-baseline<.10,kill_refit=da<-.02 or dt<-.02,
  missing_nonstatus_cues='unmeasured, never substituted with candidate proxies',
  reused_study=str(gate.ROOT/'o3_cache/out/CUE_STUDY.md'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--rows',required=True);p.add_argument('--inventory',required=True);p.add_argument('--manifest',required=True);p.add_argument('--fit',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 rules=Path(__file__).resolve().parents[1]/'out/K1_RULES.json'
 if json.loads(rules.read_text())!=RULES or gate.sha(rules)!=(rules.with_suffix('.sha256').read_text().split()[0]):raise ValueError('Preregistration changed')
 manifest=json.loads(Path(a.manifest).read_text());fit=json.loads(Path(a.fit).read_text())
 if manifest['inventory']['sha256']!=gate.sha(a.inventory) or fit.get('fixture_only') is not False:raise ValueError('K1 manifest or fit provenance differs')
 ids=[r['id'] for c in manifest['captures'] for r in c['rows']]
 if len(set(ids))!=len(ids):raise ValueError('Duplicate planned K1 IDs')
 r=report([json.loads(l) for l in open(a.rows)],json.loads(Path(a.inventory).read_text()),fit,ids)
 r['rules_sha256']=gate.sha(rules);Path(a.out).write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()
