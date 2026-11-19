"""Verbatim bootstrap from the supplied score_r5.py."""
import random
from collections import defaultdict
import numpy as np

def bootstrap(pairs):
    groups=defaultdict(list)
    for room,value in pairs:groups[room].append(float(value))
    if not groups:return dict(value=None,ci95=None,ci9929=None,upper95=None,n=0,rooms=0)
    groups=[groups[k] for k in sorted(groups)]
    sums=np.array([sum(g) for g in groups]);counts=np.array([len(g) for g in groups])
    # Match the accepted room_bootstrap.py RNG and ratio estimator.
    rng=random.Random(17);samples=[];grouped=list(zip(sums.tolist(),counts.tolist()))
    for _ in range(10000):
        draw=rng.choices(grouped,k=len(grouped))
        samples.append(sum(v[0] for v in draw)/sum(v[1] for v in draw))
    return dict(value=float(sums.sum()/counts.sum()),ci95=np.quantile(samples,[.025,.975]).tolist(),
                ci9929=np.quantile(samples,[.00355,.99645]).tolist(),upper95=float(np.quantile(samples,.95)),n=int(counts.sum()),rooms=len(groups))
