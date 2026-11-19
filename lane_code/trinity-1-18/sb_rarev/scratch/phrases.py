import sys,json,re
sys.dont_write_bytecode=True
sys.path.insert(0,'.')
from leak import toks,STOP,HELDOUT,W,T
GENERIC={('camera','orientation'),('camera','position'),('signed','degree'),('frame','frame'),('left','positive')}
def cb(s):
  ts=[t for t in toks(s) if t not in STOP and t not in ('frame','RANGE','clip','video','sequence','displayed','frames','degree','degrees','meters','unit')]
  return {(a,b) for a,b in zip(ts,ts[1:])}
for t in T:
  tr=set().union(*[cb(s) for s in W['training'][t]])
  for k,h in enumerate(HELDOUT[t]):
    sh=sorted(cb(h)&tr-GENERIC)
    print(t[7:10],f'h{k:02d}',len(sh),sh)
