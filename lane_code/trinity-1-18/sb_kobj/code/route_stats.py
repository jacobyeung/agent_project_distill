"""Predeclared room bootstrap, route bars, and one-look reservation."""
import numpy as np
from collections import defaultdict
from common import *

def paired(rows,reference='direct_score'):
 if not rows:return dict(status='MISSING',head=None,direct=None,difference=None,ci95=None,n=0)
 assert len({r['qid'] for r in rows})==len(rows)
 assert all(r['head_score'] is not None and r[reference] is not None for r in rows)
 rooms=sorted({r['room'] for r in rows});idx={r:i for i,r in enumerate(rooms)}
 c=np.array([idx[r['room']] for r in rows]);a=np.array([r['head_score'] for r in rows]);b=np.array([r[reference] for r in rows])
 assert np.isfinite(a).all() and np.isfinite(b).all() and ((a>=0)&(a<=1)&(b>=0)&(b<=1)).all()
 total=np.bincount(c,weights=a-b,minlength=len(rooms));count=np.bincount(c,minlength=len(rooms))
 rng=np.random.default_rng(20261119);draw=rng.integers(len(rooms),size=(10000,len(rooms)));boot=100*total[draw].sum(1)/count[draw].sum(1)
 return dict(status='OK',head=100*float(a.mean()),direct=100*float(b.mean()),difference=100*float((a-b).mean()),ci95=np.percentile(boot,[2.5,97.5]).tolist(),n=len(rows),rooms=len(rooms),draws=10000,seed=20261119,refusals=sum(bool(r['refusal_code']) for r in rows))

def verdict(typ,summary,gate,arm='g3t_s4',variant='fallback',comparison='direct',box_rule='today'):
 if summary['status']!='OK':return 'MISSING'
 d=summary['difference'];lo,hi=summary['ci95']
 if arm=='da3_f32':return 'CONTEXT_ONLY'
 if typ=='object_counting':return 'DIAGNOSTIC_ONLY: sb_countdesign owns route'
 if comparison=='track_vs_present':return 'REPLACE_SOURCE' if lo>0 else 'KEEP_PRESENT'
 if typ=='object_abs_distance':
  if comparison=='object_vs_today':return 'CONFIRM_OBJECT' if lo>0 else ('WITHDRAW_KIT1_PASS' if hi<0 else 'UNDECIDED')
  if comparison=='T94_vs_f32':return 'PAYS' if lo>0 else 'DOES_NOT_PAY'
  return 'CONTEXT_ONLY'
 if typ=='object_size_estimation' and ((not gate['size_screen'] and not gate['object_exists']) or (box_rule=='today' and not gate['object_exists'])):return 'REPORT_ONLY: size screen/object gate'
 if typ=='obj_appearance_order' and (not gate['first_seen_screen'] or variant=='strict'):return 'REPORT_ONLY'
 if typ=='object_rel_distance' and variant=='full':return 'REPORT_ONLY'
 threshold=3 if typ=='object_rel_distance' else 5
 if d>=threshold and lo>0:return 'ROUTE'
 if hi<0:return 'STAYS_DIRECT'
 return 'UNDECIDED: direct'

def revsi(typ,subtype_summaries):
 path=ROOT/'inputs/REVSI_SUBTYPE_WEIGHTS.json'
 if not path.exists():return dict(status='MISSING',expected_path=str(path),points=None)
 weights=js(path);ww=weights['weights'][typ]
 if set(ww)!=set(subtype_summaries):raise ValueError('Subtype weight coverage mismatch')
 assert abs(sum(ww.values())-1)<1e-9
 return dict(status='OK',points=sum(ww[k]*subtype_summaries[k]['difference'] for k in ww)/7)

def reserve_look(split,typ,registration):
 path=ROOT/'out/object_route/looks'/f'{split}__{typ}.json';path.parent.mkdir(parents=True,exist_ok=True)
 # Exclusive create: an interrupted/finished category cannot silently get another look.
 with path.open('x') as f:json.dump(dict(registration=registration,input_sha256=dict(PINS)),f,indent=2)

def report(rows,gate):
 groups=defaultdict(list)
 for row in rows:groups[(row['split'],row['dataset'],row['type'],row['arm'],row['box_rule'],row['variant'])].append(row)
 table=[]
 for key,rr in sorted(groups.items()):
  split,dataset,typ,arm,box,variant=key
  scored=[r for r in rr if r['head_score'] is not None and r.get('direct_score') is not None]
  summary=paired(scored) if len(scored)==len(rr) else dict(status='MISSING',n=len(rr),head=None,direct=None,difference=None,ci95=None)
  v=verdict(typ,summary,gate,arm,variant,box_rule=box)
  sub={s:paired([r for r in scored if r['subtype']==s]) for s in sorted({r['subtype'] for r in scored})}
  row=dict(split=split,dataset=dataset,category=typ,arm=arm,box_rule=box,variant=variant,summary=summary,verdict=v,revsi=revsi(typ,sub) if sub else dict(status='MISSING',points=None))
  if typ=='object_rel_distance' and variant=='fallback':
   changed=[r for r in scored if r['prediction']!=r['direct_prediction']];row['changes']=dict(changed=len(changed),became_right=sum(r['head_score']>r['direct_score'] for r in changed),became_wrong=sum(r['head_score']<r['direct_score'] for r in changed))
  if typ=='object_counting':row['truth_bands']={str(v):paired([r for r in scored if (int(float(r['truth'])) if int(float(r['truth']))<5 else 5)==v]) for v in (2,3,4,5)}
  if typ=='object_abs_distance':
   row['context']=dict(constant_points=29.5,head_points=100*float(np.mean([r['head_score'] for r in rr])) if all(r['head_score'] is not None for r in rr) else None,D0_points=100*float(np.mean([r['d0_score'] for r in rr])) if all(r.get('d0_score') is not None for r in rr) else None,paired_decision=False)
  table.append(row)
 # Match all paired arm comparisons by qid and require complete identical item sets.
 for key,rr in sorted(groups.items()):
  split,ds,typ,arm,box,variant=key;refkey=None;comparison=None
  if arm=='track':refkey=(split,ds,typ,'g3t_s4',box,variant);comparison='track_vs_present'
  elif arm=='T94' and typ=='object_abs_distance':refkey=(split,ds,typ,'g3t_s4',box,variant);comparison='T94_vs_f32'
  elif arm=='g3t_s4' and box=='object' and typ=='object_abs_distance':refkey=(split,ds,typ,arm,'today',variant);comparison='object_vs_today'
  if refkey is None:continue
  ref={r['qid']:r for r in groups.get(refkey,[])};same=set(ref)=={r['qid'] for r in rr};pairs=[]
  if same:
   for r in rr:
    b=ref[r['qid']];assert b['room']==r['room'] and b['truth']==r['truth']
    if r['head_score'] is not None and b['head_score'] is not None:pairs.append(dict(r,reference_score=b['head_score']))
  summary=paired(pairs,'reference_score') if same and len(pairs)==len(rr) else dict(status='MISSING',n=len(rr),head=None,direct=None,difference=None,ci95=None)
  table.append(dict(split=split,dataset=ds,category=typ,arm=arm,box_rule=box,variant=variant,comparison=comparison,summary=summary,verdict=verdict(typ,summary,gate,arm,variant,comparison,box)))
 return table
