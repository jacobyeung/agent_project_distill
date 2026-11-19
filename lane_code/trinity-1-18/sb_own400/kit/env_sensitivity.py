"""Find the first uniform scale perturbation that triggers the immutable Q2 rule."""
import os,sys
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='8'
os.environ['CUDA_VISIBLE_DEVICES']='';sys.dont_write_bytecode=True
import argparse,time
import numpy as np
from collections import defaultdict
from core import *
from score_400 import module,S1,summarize,choose

def prepare(s,bars,pins):
 cs={c['canonical']:c for c in s.training()};records=[];missing=[]
 for n,r in enumerate(bars['captures']):
  c=cs[r['canonical']];assert digest(c)==r['capture_sha256']
  if not r['gt_present']:missing.append(c['gt']);continue
  for q in (r['tower'],r['own544']):checked(q['path'],q['sha256']);pins[q['path']]=q['sha256']
  checked(c['gt']['path'],c['gt']['sha256']);pins[c['gt']['path']]=c['gt']['sha256']
  with np.load(c['gt']['path']) as z:gt={k:z[k] for k in ('c2w','valid','frame_indices')}
  with np.load(r['tower']['path']) as z:t={k:z[k] for k in ('raw_pose','depth_grid','depth_conf_grid','anchor_slots','frame_indices')}
  with np.load(r['own544']['path']) as z:dep=z['depth']
  assert np.array_equal(gt['frame_indices'],c['anchor_indices']) and np.array_equal(t['frame_indices'][t['anchor_slots']],c['anchor_indices'])
  scale=s.estimate(t['depth_grid'],t['depth_conf_grid'],dep)[0]
  _,centres,_=s.to_gravity_reference_frame(t['raw_pose'][t['anchor_slots']],[0.,-1.,0.])
  i,j=np.triu_indices(32,1);truth=np.linalg.norm(gt['c2w'][i,:3,3]-gt['c2w'][j,:3,3],axis=1)
  ok=gt['valid'][i].astype(bool)&gt['valid'][j].astype(bool)&np.isfinite(truth)&(truth>=.1)
  raw=np.linalg.norm(centres[i]-centres[j],axis=1)[ok]
  records.append({'capture':c['canonical'],'room':c['room'],'gt':truth[ok],'pred':{'A':raw*scale}})
  if (n+1)%40==0:print('Sensitivity loaded',n+1,flush=True)
 return records,missing

def event_search(records,folds,direction=1):
 """Sweep every score boundary from 1. Bootstrap samples use the original seed/order.

 A score can change only at (1 +/- threshold)*GT/A. Entry events improve B;
 only exit events can make its upper CI cross below zero. No monotonicity assumption.
 """
 rooms=sorted({r['room'] for r in records});ri={r:i for i,r in enumerate(rooms)}
 counts=np.array([sum(len(r['gt']) for r in records if r['room']==room) for room in rooms])
 groups=[sorted(set(f['test_rooms'])&set(rooms)) for f in folds]+[rooms]
 weights=[]
 for group in groups:
  n=len(group);draws=np.random.default_rng(17).integers(0,n,size=(10000,n))
  w=np.zeros((10000,len(rooms)),dtype=np.float64)
  for j,room in enumerate(group):w[:,ri[room]]=(draws==j).sum(axis=1)/n
  weights.append(w)
 samples=[np.zeros(10000) for _ in groups];means=np.zeros(len(rooms))
 events=[]
 thresholds=np.array([(100-t)/100 for t in range(50,100,5)])
 for r in records:
  base=r['pred']['A'];gt=r['gt'];good=base>0;ratio=gt[good]/base[good]
  for sign in (-1,1):
   values=(ratio[:,None]*(1+sign*thresholds)).ravel()
   # Ascending: lower boundary enters (+), upper exits (-); descending reverses.
   delta=-sign*direction
   for v in values[(values>1) if direction==1 else ((values<1)&(values>0))]:events.append((float(v),ri[r['room']],delta))
 events.sort(key=lambda x:direction*x[0]);visited=0;idx=0
 while idx<len(events):
  value=events[idx][0];changes=defaultdict(int)
  while idx<len(events) and events[idx][0]==value:
   _,room,delta=events[idx];changes[room,delta]+=1;idx+=1
  # At the exact boundary exits happen; entries require moving strictly past it.
  for phase in (-1,1):
   changed=False
   for (room,delta),n in changes.items():
    if delta!=phase:continue
    step=10.*delta*n/counts[room];means[room]+=step
    for sample,w in zip(samples,weights):sample+=step*w[:,room]
    changed=True
   if phase==-1 and changed:
    visited+=1
    if all(np.quantile(sample,.975)<-1e-10 for sample in samples):
     # Verify with the source scorer at this boundary and its adjacent floats.
     for candidate in (value,np.nextafter(value,np.inf if direction==1 else 0.)):
      for r in records:r['pred']['B']=r['pred']['A']*candidate
      reports=[summarize_source(records,set(group)) for group in groups]
      if choose(reports[:2],reports[2])==544:
       return {'multiplier':candidate,'percent_shift':100*(candidate-1),'boundary':value,'boundaries_checked':visited,'events_swept':idx,'B-A':[r['B-A'] for r in reports]}
  if visited and visited%5000==0:print('Boundaries',direction,visited,'multiplier',value,flush=True)
 return {'status':'MISSING: no multiplier in positive direction domain passed','boundaries_checked':visited}

_SOURCE=None
def summarize_source(records,rooms):return summarize(_SOURCE,[r for r in records if r['room'] in rooms])
def main():
 global _SOURCE
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--cache',type=pathlib.Path);a=ap.parse_args();out=fresh(a.out)
 bars=read(ROOT/'out/BARS_FROZEN.json');vb=read(ROOT/'out/BARS_FROZEN_B.json');checked(ROOT/'out/BARS_FROZEN.json',vb['input_sha256'][str(ROOT/'out/BARS_FROZEN.json')])
 pins={str(p):sha(p) for p in (S1,pathlib.Path(__file__),KIT/'score_400.py',ROOT/'out/BARS_FROZEN.json',ROOT/'out/BARS_FROZEN_B.json')}
 _SOURCE=module(S1,'sensitivity_source');checked(S1,bars['code_sha256'])
 pins.update({str(p):sha(p) for p in (_SOURCE.HARNESS,_SOURCE.CAMERA,_SOURCE.RULE_CODE,_SOURCE.MANIFEST)})
 start=time.monotonic()
 if a.cache:
  rec=read(a.cache/'PAIR_INPUTS.json');pins.update(rec['input_sha256']);checked(a.cache/'pairs.npz',rec['pairs_sha256']);pins[str(a.cache/'PAIR_INPUTS.json')]=sha(a.cache/'PAIR_INPUTS.json')
  with np.load(a.cache/'pairs.npz') as z:records=[{'room':room,'capture':cap,'gt':z['gt'][lo:hi],'pred':{'A':z['pred'][lo:hi]}} for room,cap,lo,hi in rec['records']]
  missing=rec['missing']
 else:
  records,missing=prepare(_SOURCE,bars,pins);offset=0;index=[]
  for r in records:index.append([r['room'],r['capture'],offset,offset+len(r['gt'])]);offset+=len(r['gt'])
  with (out/'pairs.npz').open('xb') as f:np.savez(f,gt=np.concatenate([r['gt'] for r in records]),pred=np.concatenate([r['pred']['A'] for r in records]))
  atomic(out/'PAIR_INPUTS.json',{'input_sha256':pins,'pairs_sha256':sha(out/'pairs.npz'),'records':index,'missing':missing})
 result={'input_sha256':pins,'synthetic':True,'meaning':'B=m*A OwnDepthScale, not real 400; step544 reference remains unmodified','captures':len(records),'rooms':len({r['room'] for r in records}),'pairs':sum(len(r['gt']) for r in records),'missing':missing}
 for direction,name in [(1,'smallest_increase'),(-1,'closest_decrease')]:
  result[name]=event_search(records,bars['folds'],direction)
  atomic(out/'ENV_SENSITIVITY.json',{**result,'seconds':time.monotonic()-start,'command':' '.join(sys.argv)})
  print(name,result[name],flush=True)
if __name__=='__main__':main()
