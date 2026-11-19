"""Training-only score policy and fail-closed prerequisites for ruling 0749Z."""
from common import *
import numpy as np
from scoring import Scorer
SCORER = Scorer()

def score(prediction, truth):
 return SCORER({'type':'object_abs_distance','gt':truth}, prediction)

def score_pair(candidate, baseline, rebuilt):
 if candidate['row_id'] != baseline['row_id'] or candidate['room'] != baseline['room'] or candidate['label'] != baseline['label']:
  raise ValueError('Unpaired rows')
 own = baseline.get('score', score(baseline['prediction'], baseline['label']))
 return (score(candidate['prediction'],candidate['label']), own) if rebuilt else (own, own)

def interval(values, rooms):
 if not values:return dict(status='MISSING',n=0,estimate=None,ci95=None)
 names=sorted(set(rooms));lookup={r:i for i,r in enumerate(names)}
 cluster=[lookup[r] for r in rooms]
 sums=np.bincount(cluster,weights=values,minlength=len(names));counts=np.bincount(cluster,minlength=len(names))
 draws=np.random.default_rng(20261119).integers(len(names),size=(10000,len(names)))
 samples=sums[draws].sum(1)/counts[draws].sum(1)
 return dict(status='OK',n=len(values),rooms=len(names),estimate=float(np.mean(values)),ci95=np.percentile(samples,[2.5,97.5]).tolist(),draws=10000,seed=20261119)

def contrast(left, right, rebuilt):
 a={r['row_id']:r for r in left};b={r['row_id']:r for r in right}
 if len(a)!=len(left) or len(b)!=len(right) or set(a)!=set(b):raise ValueError('Full paired denominator required')
 ids=sorted(a);pairs=[score_pair(a[i],b[i],rebuilt[b[i]['capture']]) for i in ids]
 stat=interval([100*(x-y) for x,y in pairs],[b[i]['room'] for i in ids])
 return dict(stat,arm_score=100*float(np.mean([x for x,y in pairs])),A0_score=100*float(np.mean([y for x,y in pairs])),retained_A0_rows=sum(not rebuilt[b[i]['capture']] for i in ids),refusals=sum(a[i]['prediction'] is None for i in ids))

def detector(row):
 """The pilot's explicit signal; no guessed thresholds for its ranking features."""
 frames=row.get('member_frames')
 if not frames:return None
 return min(map(len,frames.values())) < 3

def doubt(left, right, rebuilt):
 a={r['row_id']:r for r in left};b={r['row_id']:r for r in right}
 if set(a)!=set(b):raise ValueError('Full paired denominator required')
 triggered=[];both=[];switched=[];missing_signal=[]
 for rid in sorted(b):
  first=b[rid];second=a[rid];signal=detector(first)
  if signal is None:missing_signal.append(rid)
  active=bool(signal) and rebuilt[first['capture']]
  # A refused second call retains the first numeric response.
  switched.append(second if active and second['prediction'] is not None else first)
  if not active:continue
  triggered.append(rid)
  if first['prediction'] is None or second['prediction'] is None:continue
  x=abs(first['prediction']-first['label']);y=abs(second['prediction']-first['label'])
  both.append(dict(row_id=rid,room=first['room'],first=first['prediction'],second=second['prediction'],truth=first['label'],closer=y<x,worse=y>x,tie=y==x,first_wrong=x/first['label']>.25))
 rooms=[r['room'] for r in both]
 return dict(detector='min grounded operand frames < 3',registered_rows=len(b),triggered=len(triggered),paired_numeric=len(both),second_refusals=sum(a[i]['prediction'] is None for i in triggered),first_refusals=sum(b[i]['prediction'] is None for i in triggered),missing_signal=missing_signal,closer=sum(r['closer'] for r in both),worse=sum(r['worse'] for r in both),ties=sum(r['tie'] for r in both),closer_rate=interval([float(r['closer']) for r in both],rooms),closer_minus_worse=interval([float(r['closer'])-float(r['worse']) for r in both],rooms),repair_gain=contrast(switched,right,rebuilt),paired=both)

def require_size_screen(path, construction):
 d=js(path)
 if d.get('status')!='COMPLETE' or d.get('selection_split')!='K1-train' or d.get('construction')!=construction:
  raise Missing('Selected construction needs its own complete K1 training size screen: '+str(path))
 if set(d.get('geometries',{}))!={'serving','g3t_s4'}:raise Missing('Both geometries required')
 for g in d['geometries'].values():
  if g.get('object_set_sha256')!=d.get('object_set_sha256') or not g.get('refusals_score_zero'):
   raise Missing('Size screen requires one fixed object set and zero-scored refusals')
 if not d.get('object_set_sha256') or d['treatment']['ci95'][0]<=-2 or not d['size_screen_pass']:
  raise Missing('Size screen or treatment gate failed')
 return d

def package_d(path):
 d=js(path)
 if d.get('status')!='BOUND':raise Missing('cont_ops18 package-D present-path returns: '+d['expected_location'])
 if d.get('lane')!='cont_ops18' or d.get('package')!='D':raise ValueError('Wrong present-path package')
 for item in d['returns']:
  if item['step'] not in (200,544) or item['original_wording_twins']!=290 or item['reworded_items']!=290:raise ValueError('Wrong package-D identity')
  if sha(item['path'])!=item['sha256']:raise ValueError('Package-D return changed')
 return d
