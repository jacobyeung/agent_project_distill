"""Independent stdlib reference for the documented R1 bootstrap specification.
This is a new reference calculation, not the unavailable accepted room_bootstrap.py.
It expands sampled rooms to items and computes quantiles without NumPy.
"""
import math
import random
import statistics


def paired(left, right, seed=17):
    a={r['key']:r for r in left};b={r['key']:r for r in right}
    if len(a)!=len(left) or len(b)!=len(right):raise ValueError('Duplicate keys')
    rooms={}
    for key in sorted(a.keys() & b.keys()):
        if a[key]['room']!=b[key]['room']:raise ValueError('Paired room differs')
        rooms.setdefault(a[key]['room'],[]).append(100*(a[key]['score']-b[key]['score']))
    groups=[rooms[k] for k in sorted(rooms)]
    if not groups:raise ValueError('No pairs')
    rng=random.Random(seed);draws=[]
    for _ in range(10000):
        sample=[]
        for _ in groups:sample.extend(groups[int(rng.random()*len(groups))])
        draws.append(statistics.mean(sample))
    draws.sort()
    def quantile(p):
        index=(len(draws)-1)*p;lo=int(math.floor(index));hi=int(math.ceil(index))
        return draws[lo]+(draws[hi]-draws[lo])*(index-lo)
    return dict(value=statistics.mean([v for g in groups for v in g]),
                ci95=[quantile(.025),quantile(.975)],
                ci9929=[quantile(.00355),quantile(.99645)],upper95=quantile(.95))
