"""Exact item pairs; 10,000 physical-room bootstrap draws; no decisions from GT stand-ins."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import argparse,collections

def interval(pairs,seed=20261112,draws=10000):
 groups=collections.defaultdict(list)
 for room,a,b in pairs:groups[room].append(b-a)
 if not groups:return None
 keys=sorted(groups);sums=np.array([sum(groups[k]) for k in keys]);ns=np.array([len(groups[k]) for k in keys]);rng=np.random.default_rng(seed)
 boot=[]
 for start in range(0,draws,250):
  ix=rng.integers(0,len(keys),(min(250,draws-start),len(keys)));boot.extend(sums[ix].sum(1)/ns[ix].sum(1))
 lo,hi=np.quantile(boot,[.025,.975]);mean=sums.sum()/ns.sum()
 return dict(difference_pp=float(mean*100),low_pp=float(lo*100),high_pp=float(hi*100),rooms=len(keys),items=int(ns.sum()),verdict=('route' if lo>0 else 'direct' if hi<0 else 'undecided'))

def index(rs,key):
 out={}
 for r in rs:
  k=key(r)
  if k in out:raise ValueError('Duplicate key '+str(k))
  out[k]=r
 return out

def checked_score(v):
 if isinstance(v,bool) or not isinstance(v,(float,int)) or not np.isfinite(v) or not 0<=v<=1:raise ValueError('Invalid/missing score')
 return float(v)

def build(items,direct,program,standin=False,seed=20261112):
 tasks=index(items,lambda r:r['qid']);d=index(direct['rows'],lambda r:r['key'].removeprefix('devrows:'))
 prs=[r for r in program if r['source']=='g3t' and r['policy']=='frozen']
 if any(r.get('stub') for r in prs):raise ValueError('Stub rows cannot enter route tables')
 pp=index(prs,lambda r:(r['qid'],r.get('arm','gt')));primary_arm='gt' if standin else 'predicted'
 eligible={q for q in d if q in tasks and tasks[q]['stratum']=='primary'}
 available={q for q,a in pp if a==primary_arm}
 missing=sorted(eligible-available)
 if missing and not standin:raise ValueError('Missing predicted rows for paired direct items: '+str(missing[:10]))
 ids=sorted(eligible&available);groups=collections.defaultdict(list);paired=[]
 for qid in ids:
  q=tasks[qid];a=d[qid];b=pp[qid,primary_arm]
  if (a['question_type'],a['room'],a['stratum'])!=(q['question_type'],q['room'],q['stratum']) or (b['type'],b['room'],b['dataset'],b['scene'],b['stratum'])!=(q['question_type'],q['room'],q['dataset'],q['scene'],q['stratum']):raise ValueError('Pair metadata mismatch '+qid)
  if b.get('released_answer')!=q['released_answer_in_options']:raise ValueError('Released label mismatch '+qid)
  x=checked_score(a['scores']['released_answer']);y=checked_score(b['score']);r=dict(qid=qid,room=q['room'],dataset=q['dataset'],type=q['question_type'],direct=x,program=y,no_answer=b['no_answer'])
  paired.append(r)
  for ds in ['All',q['dataset']]:groups[ds,q['question_type']].append(r)
 table=[]
 for (ds,t),rs in sorted(groups.items()):
  result=interval([(r['room'],r['direct'],r['program']) for r in rs],seed)
  result.update(dataset=ds,type=t,direct_pct=100*float(np.mean([r['direct'] for r in rs])),program_pct=100*float(np.mean([r['program'] for r in rs])),no_answers=sum(r['no_answer'] for r in rs),fallback_program_pct=100*float(np.mean([r['direct'] if r['no_answer'] else r['program'] for r in rs])))
  result['rule_verdict']=result.pop('verdict');result['decision']='not_a_decision_upper_bound' if standin else result['rule_verdict']
  table.append(result)
 # Telescoping losses. Mask/identity residual prevents mislabelling non-accept errors.
 decomposition=[]
 for (ds,t),rs in sorted(groups.items()):
  arms=['predicted','oracle_accept','gt_proposed','gt_ever_proposed','gt'];keep=[r for r in rs if all((r['qid'],a) in pp for a in arms)]
  if not keep:continue
  for name,a,b in [('wrong_object_accepted','predicted','oracle_accept'),('mask_shape_and_identity_residual','oracle_accept','gt_proposed'),('fewer_frames','gt_proposed','gt_ever_proposed'),('object_never_proposed','gt_ever_proposed','gt')]:
   rr=interval([(r['room'],checked_score(pp[r['qid'],a]['score']),checked_score(pp[r['qid'],b]['score'])) for r in keep],seed);decomposition.append(dict(dataset=ds,type=t,component=name,**rr))
 return dict(status='UPPER BOUND STAND-IN — NOT A ROUTING DECISION' if standin else 'predicted-mask paired route table',score='released labels; primary stratum; raw program; no-answer=0; direct fallback descriptive only',bootstrap=dict(unit='physical room',draws=10000,seed=seed,method='percentile, resampled rooms with item-weighted mean'),direct_model=direct['model'],direct_arm=direct['arm'],direct_binding=direct['request_binding'],paired_items=len(ids),eligible_direct_items=len(eligible),missing_program_qids=missing,program_only_items=len(available-set(d)),table=table,decomposition=decomposition,paired=paired)

def markdown(d):
 s=[d['status'],'',d['score']+'.','',f"Pairs: {d['paired_items']} of {d['eligible_direct_items']} eligible direct items; {len(d['missing_program_qids'])} missing program/GT rows. Room percentile bootstrap: 10,000 draws, seed {d['bootstrap']['seed']}.",'','| Dataset | Type | Items / rooms | Direct % | Program % | Difference pp [95% CI] | Rule verdict* |','|---|---|---:|---:|---:|---|---|']
 for r in d['table']:s.append(f"| {r['dataset']} | {r['type']} | {r['items']} / {r['rooms']} | {r['direct_pct']:.1f} | {r['program_pct']:.1f} | {r['difference_pp']:+.1f} [{r['low_pp']:+.1f}, {r['high_pp']:+.1f}] | {r['rule_verdict']} |")
 s+=['','*GT-mask stand-in verdicts are diagnostic only. GT masks are an oracle reference, not a mathematical score bound. No predicted-mask decision is available.' if d['status'].startswith('UPPER') else '*Route only when the interval is strictly above zero; direct only when strictly below; zero-inclusive intervals are undecided. Room counts disclose low-support and degenerate intervals.','', 'Loss decomposition is unavailable for the GT stand-in. The source GT pricing aligned tower pose to GT by yaw/translation. The deployment kit uses raw exported coordinates; voxel bins and floor cells can change under this alignment (see REPLAY_PARITY.json).' if not d['decomposition'] else 'The JSON reports paired score contrasts for wrong-object accepts, mask/identity residual, fewer matched frames, and never-proposed instances. These counterfactual contrasts can be negative and are not additive error counts.']
 return '\n'.join(s)+'\n'

def main():
 p=argparse.ArgumentParser(__doc__)
 for n in ['items','direct','program','out']:p.add_argument('--'+n,required=True)
 p.add_argument('--stand-in',action='store_true');a=p.parse_args()
 result=build(rows(a.items),json.loads(Path(a.direct).read_text()),rows(a.program),a.stand_in)
 out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);dump(out.with_suffix('.json'),result);out.with_suffix('.md').write_text(markdown(result));write_rows(out.with_suffix('.pairs.jsonl'),result['paired']);print(json.dumps(dict(pairs=result['paired_items'],table_rows=len(result['table']),missing=len(result['missing_program_qids']))))
if __name__=='__main__':main()
