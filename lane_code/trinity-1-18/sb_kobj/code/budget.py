"""Cumulative arm budget. An interrupted reservation stays charged and requires review."""
from common import *
BUDGETS={'R0_f32':10800,'T94':10080,'track':14400,'dev-S1':7200}
GROUPS={'r0_g3t':'R0_f32','r0_sam':'R0_f32','T94_g3t':'T94','T94_sam':'T94','track':'track','s1_g3t':'dev-S1','s1_sam':'dev-S1'}

def remaining(group):
 p=ROOT/'out/object_route/budgets'/f'{group}.json'
 if not p.exists():return BUDGETS[group]
 d=js(p)
 if d.get('active'):raise Missing('Interrupted or active budget reservation: '+str(p)+'; no automatic rerun')
 return max(0,BUDGETS[group]-d['seconds'])

def begin(group):
 seconds=remaining(group)
 if seconds<=0:raise Missing('Arm budget exhausted: '+group)
 write(ROOT/'out/object_route/budgets'/f'{group}.json',dict(active=True,seconds=BUDGETS[group]-seconds,remaining_at_start=seconds,start_unix=time.time()));return time.monotonic(),seconds

def end(group,start):
 p=ROOT/'out/object_route/budgets'/f'{group}.json';d=js(p);write(p,dict(active=False,seconds=d['seconds']+time.monotonic()-start))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('step',choices=GROUPS);a=p.parse_args();print(int(remaining(GROUPS[a.step])))
