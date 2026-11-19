"""Registered item-weighted room bootstrap and benchmark mappings."""
from collections import defaultdict
import numpy as np
from common import *

def paired(rows,reference='direct_score'):
 if not rows:return dict(status='MISSING',head=None,direct=None,difference=None,ci95=None,n=0)
 ids=[r.get('source_line',r['qid']) for r in rows];assert len(set(ids))==len(ids)
 rooms=sorted({r['room'] for r in rows});idx={r:i for i,r in enumerate(rooms)}
 c=np.array([idx[r['room']] for r in rows]);a=np.array([r['head_score'] for r in rows],dtype=np.float64);b=np.array([r[reference] for r in rows],dtype=np.float64)
 assert np.isfinite(a).all() and np.isfinite(b).all() and ((a>=0)&(a<=1)&(b>=0)&(b<=1)).all()
 total=np.bincount(c,weights=a-b,minlength=len(rooms));count=np.bincount(c,minlength=len(rooms))
 rng=np.random.default_rng(20261119);draw=rng.integers(len(rooms),size=(10000,len(rooms)));boot=100*total[draw].sum(1)/count[draw].sum(1)
 return dict(status='OK',head=100*float(a.mean()),direct=100*float(b.mean()),difference=100*float((a-b).mean()),ci95=np.percentile(boot,[2.5,97.5]).tolist(),n=len(rows),rooms=len(rooms),draws=10000,seed=20261119,refusals=sum(bool(r['refusal_code']) for r in rows))

def summary(typ,rows,arm,diagnostic=False):
 s=paired(rows);subs={k:paired([r for r in rows if r['subtype']==k]) for k in sorted({r['subtype'] for r in rows})}
 if typ=='obj_appearance_order':revsi=None
 elif typ=='object_rel_distance':
  assert set(subs)=={'closest','farthest'}
  revsi=sum(x['difference'] for x in subs.values())/2/7
 else:revsi=s['difference']/7
 changed=[r for r in rows if r['prediction']!=r['direct_prediction']]
 verdict='DIAGNOSTIC_ONLY' if diagnostic else 'PASS' if s['difference']>=arm['bar']['type_points'] and s['ci95'][0]>0 else 'MISS'
 return dict(category=typ,arm=arm,present_path='present call' if typ=='object_abs_distance' else 'direct answer',treatment='S4 treatment',summary=s,subtypes=subs,ReVSI_points=revsi,VSI_Bench_points=s['difference']/8,verdict=verdict,answers_changed=len(changed),became_right=sum(r['head_score']>r['direct_score'] for r in changed),became_wrong=sum(r['head_score']<r['direct_score'] for r in changed))
