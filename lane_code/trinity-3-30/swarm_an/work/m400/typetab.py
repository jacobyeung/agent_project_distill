import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
from collections import defaultdict
T=defaultdict(dict)
for s in ('dev-S1','R0-dev'):
    for run,st in (('S1',544),('R1',100),('R1',200),('R1',400)):
        for ty,v in K.summary(K.direct(run,st,s)).items(): T[(s,ty)][st]=(v['items'],v['score_pct'],v['forced_close'])
P=defaultdict(lambda: defaultdict(lambda:[0,0.0]))
for (s,ty),d in sorted(T.items()):
    print('%-7s %-32s'%(s,ty),' | '.join('%d: %.1f (n%d fc%d)'%(st,v[1],v[0],v[2]) for st,v in sorted(d.items())))
    for st,v in d.items(): P[ty][st][0]+=v[0]; P[ty][st][1]+=v[0]*v[1]
print('pooled (item-weighted)')
for ty,d in sorted(P.items()):
    x={st:v[1]/v[0] for st,v in d.items()}
    print('%-32s'%ty,' | '.join('%d: %.1f'%(st,x[st]) for st in sorted(x)), ' d200->400 %+.1f'%(x.get(400,0)-x.get(200,0)))
