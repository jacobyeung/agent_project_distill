"""Cumulative hard stops and admission against the three-kit 16-hour ledger."""
from common import *
BUDGETS={'K1_track':6300,'R0_f32':12600,'track':11700,'T94':10800,'dev-S1':7200,'S1_track':3600}
ESTIMATES={'K1_track':1.3,'R0_f32':3.,'track':3.,'T94':2.8,'dev-S1':2.,'S1_track':1.}
GROUPS={'k1_track':'K1_track','r0_g3t':'R0_f32','r0_sam':'R0_f32','track':'track','T94_g3t':'T94','T94_sam':'T94','s1_g3t':'dev-S1','s1_sam':'dev-S1','s1_track':'S1_track'}
LEDGER=ROOT/'inputs/GPU_LEDGER.json'

def used():
 result=0.
 for group in BUDGETS:
  p=ROOT/'out/object_route/budgets'/f'{group}.json'
  if p.exists():
   d=js(p)
   if d.get('active'):raise Missing('Active/interrupted reservation; requires orchestrator review: '+str(p))
   result+=d['seconds']
 return result

def remaining(group):
 used();p=ROOT/'out/object_route/budgets'/f'{group}.json'
 return max(0.,BUDGETS[group]-(js(p)['seconds'] if p.exists() else 0.))

def admission(group):
 ledger=js(LEDGER)
 assert ledger['status']=='AUTHORIZED' and ledger['kit']=='sb_kobj4'
 # Exclusive lease prevents another kit spending the same remaining hours.
 assert ledger['exclusive_lease'] and ledger['excludes_this_workspace_usage']
 if time.time()>=ledger['expires_unix']:raise Missing('GPU ledger lease expired')
 seconds=remaining(group)
 if ledger['other_kits_seconds']+used()+seconds>16*3600:raise Missing('16 GPU-hour ledger cap')
 if seconds>ledger['lease_seconds']-used():raise Missing('Workspace GPU-hour lease exhausted')
 return int(seconds)

def begin(group):
 seconds=admission(group)
 if seconds<=0:raise Missing('Part budget exhausted: '+group)
 write(ROOT/'out/object_route/budgets'/f'{group}.json',dict(active=True,seconds=BUDGETS[group]-seconds,remaining_at_start=seconds,start_unix=time.time()))
 return time.monotonic(),seconds

def end(group,start):
 p=ROOT/'out/object_route/budgets'/f'{group}.json';d=js(p);write(p,dict(active=False,seconds=d['seconds']+time.monotonic()-start))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('step',choices=GROUPS);a=p.parse_args();print(admission(GROUPS[a.step]))
