"""B8: room call-rate marks by bootstrap over physical rooms (dev-S1: 36 items in 9 rooms; R0-dev: 98 items in 98 rooms).
Prints, for placements of the calling reads, the one-sided 95% upper bound of the call rate (percentile, 20,000 draws)
and the largest count that keeps the bound below 25% and below 5%."""
import json, numpy as np
R='/scratch/jjyeung/orch_n30/cont_ops/work/d0/readk'
A=[json.loads(l) for l in open(R+'/evidence/A544.jsonl') if l.strip()]
import collections
dev=sorted(collections.Counter(r['room'] for r in A if r['task_type']=='room_size_estimation').values(),reverse=True)
sizes=np.array(dev+[1]*98,dtype=float); K=len(sizes); rng=np.random.default_rng(8)
idx=rng.integers(0,K,size=(20000,K)); M=np.zeros((20000,K)); np.add.at(M,(np.repeat(np.arange(20000),K),idx.ravel()),1.0)
den=M@sizes
def ub(calls): return float(np.quantile((M@calls)/den,0.95))
out=dict(dev_room_sizes=dev,rooms=K,items=int(sizes.sum()),placements={})
def spread(k):                    # one call per room, R0-dev rooms first
    c=np.zeros(K); c[len(dev):len(dev)+min(k,98)]=1; rest=k-min(k,98)
    for i in range(len(dev)):
        t=min(rest,int(sizes[i])); c[i]=t; rest-=t
    return c
def clustered(k):                 # whole dev-S1 rooms call first (largest first), then R0-dev rooms
    c=np.zeros(K); rest=k
    for i in range(len(dev)):
        t=min(rest,int(sizes[i])); c[i]=t; rest-=t
    c[len(dev):len(dev)+rest]=1; return c
for name,f in (('spread over R0-dev rooms',spread),('clustered in dev-S1 rooms',clustered)):
    tab={k:round(100*ub(f(k)),2) for k in range(0,41)}
    out['placements'][name]=dict(upper95_pct_by_count=tab,largest_count_below_25pct=max(k for k,v in tab.items() if v<25),
                                 largest_count_below_5pct=max([k for k,v in tab.items() if v<5]))
json.dump(out,open('B8_ROOM_CALL_BOUND.json','w'),indent=1)
for n,v in out['placements'].items(): print(n,v['largest_count_below_25pct'],v['largest_count_below_5pct'],{k:v['upper95_pct_by_count'][k] for k in (0,1,2,3,4,6,12,18,24,25,26,30)})
print(dev,K)
