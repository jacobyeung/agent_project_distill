"""Exact paired function from the accepted r5 report.py (a minus b)."""
import collections
import random

def paired(a,b,field,replicates=10000,seed=17):
    if replicates < 1:raise ValueError('Replicates must be positive')
    aa={r['key']:r for r in a};bb={r['key']:r for r in b}
    if set(aa)!=set(bb):raise ValueError('Paired keys differ')
    clusters=collections.defaultdict(list)
    for key,x in aa.items():
        y=bb[key]
        if (x['room'],x['stratum'],x['question_type'])!=(y['room'],y['stratum'],y['question_type']):raise ValueError('Paired metadata differs')
        v,w=x['scores'][field],y['scores'][field]
        if v is not None and w is not None:clusters[x['room']].append(v-w)
    if not clusters:return dict(items=0,rooms=0,delta_pp=None,ci95_pp=None)
    grouped=[(sum(ds),len(ds)) for _,ds in sorted(clusters.items())]
    n=sum(v[1] for v in grouped);delta=sum(v[0] for v in grouped)/n
    rng=random.Random(seed);samples=[]
    for _ in range(replicates):
        draw=rng.choices(grouped,k=len(grouped));samples.append(sum(v[0] for v in draw)/sum(v[1] for v in draw))
    samples.sort()
    def quantile(p):
        k=(len(samples)-1)*p;i=int(k);j=min(i+1,len(samples)-1)
        return 100*(samples[i]+(samples[j]-samples[i])*(k-i))
    return dict(items=n,rooms=len(grouped),delta_pp=100*delta,ci95_pp=[quantile(.025),quantile(.975)],
                replicates=replicates,seed=seed,estimator='item-weighted mean; resample whole physical rooms with replacement, retain all paired items')
