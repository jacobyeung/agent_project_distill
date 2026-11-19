"""Predictors of the chosen option (lane san_dd_app)."""
import sys; sys.path.insert(0,'/scratch/jjyeung/orch_n30/san_dd_app/work'); import app as A
from collections import Counter, defaultdict
from itertools import combinations
def kt(a,b):
    pa={o:i for i,o in enumerate(a)}; pb={o:i for i,o in enumerate(b)}
    return sum((pa[x]<pa[y])==(pb[x]<pb[y]) for x,y in combinations(a,2))
def lcp(a,b):
    n=0
    for x,y in zip(a,b):
        if x!=y: break
        n+=1
    return n
def argmax(op, f):
    s={k:f(v) for k,v in op.items()}; m=max(s.values()); return [k for k in sorted(s) if s[k]==m]
def class_pos(P, key):
    """class -> list of (item id, position) from truth ('truth') or answer ('ans')"""
    d=defaultdict(list)
    for p in P.values():
        o=p['truth'] if key=='truth' else p['op'][p['pred']]
        for j,x in enumerate(o): d[x].append((p['id'],j))
    return d
def prior_order(p, d):
    def m(x):
        v=[j for i,j in d.get(x,[]) if i!=p['id']]
        return sum(v)/len(v) if v else 1.5
    return sorted(p['q'], key=lambda x:(m(x), p['q'].index(x)))
def predictors(p, P544, P100, dT, dA):
    op=p['op']; w=p['w']; fo=p['fo']; q=p['q']
    firsts=Counter(v[0] for v in op.values()); mf=max(firsts.values())
    return {
     'starts with written-first object': [k for k in sorted(op) if op[k][0]==w[0]],
     'starts with earliest-frame object': [k for k in sorted(op) if op[k][0]==fo[0]],
     'nearest (pairs) to written order': argmax(op, lambda v: kt(w,v)),
     'longest shared prefix with written order': argmax(op, lambda v: lcp(w,v)),
     'nearest (pairs) to frame order': argmax(op, lambda v: kt(fo,v)),
     'nearest to question order': argmax(op, lambda v: kt(q,v)),
     'starts with question-first object': [k for k in sorted(op) if op[k][0]==q[0]],
     'starts with plurality first object': [k for k in sorted(op) if firsts[op[k][0]]==mf],
     'letter A': ['A'], 'letter B': ['B'], 'letter C': ['C'], 'letter D': ['D'],
     'class prior from truth (leave-one-out)': argmax(op, lambda v: kt(prior_order(p,dT),v)),
     'class prior from answers (leave-one-out)': argmax(op, lambda v: kt(prior_order(p,dA),v)),
     'step-544 answer': [P544[p['id']]['pred']],
     'step-100 answer': [P100[p['id']]['pred']],
    }
