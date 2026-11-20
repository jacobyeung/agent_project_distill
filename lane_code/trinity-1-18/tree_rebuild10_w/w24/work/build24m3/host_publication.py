from common import *
for name in ('q','n','n_go','qd'):
 k=kit(name);s=(k/'b/h.py').read_text()
 needle="cfg['r1_training']['host_receipt']=write(r/'hr.json',host)"
 assert needle in s
 s=s.replace(needle,needle+"""
if 'protected_census' in host:
 import os
 from rv import location,put
 live,_=location(k,r.parent,os.environ['SLURM_JOB_ID'])
 put(live/'h0.json',(r/'hr.json').read_bytes())""")
 replace(k/'b/h.py',s)
 s=(k/'b/rv.py').read_text()
 needle="            pin=verify_census(kit,root,cfg)"
 s=s.replace(needle,needle+"\n            from z import checked\n            checked(live/'h0.json',cfg['r1_training']['host_receipt']['sha256'])")
 replace(k/'b/rv.py',s)
 for p in ('BUILD.json','SHA256SUMS.txt'):replace(k/p,(k/p).read_bytes())
 print(name,reseal(k))
