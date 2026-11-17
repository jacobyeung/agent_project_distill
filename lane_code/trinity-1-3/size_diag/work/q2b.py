import json, math, collections, re, statistics as st
from load import mra
rows=json.load(open('size_rows_544_m200.json'))
TO_CM={'cm':1.0,'mm':0.1,'m':100.0,'in':2.54,'ft':30.48}
def best_unit(pred, gt, u):
    gcm=gt*TO_CM[u]
    best=None
    for v,f in TO_CM.items():
        if v=='mm': continue
        # pred interpreted as unit v
        e=abs(math.log(pred*f/gcm)) if pred>0 else 99
        if best is None or e<best[1]: best=(v,e)
    return best
def form(g):
    g=g.split('</think>')[0]
    m=re.search(r'longest edge is ([\d\.]+) ?([a-z]+)',g)
    conv=re.search(r'convert to ([a-z]+): ([\d\.]+) ?([a-z]+) = ([\d\.]+) ?([a-z]+)',g)
    est='I estimate it from the frames' in g
    return m, conv, est
C=collections.Counter()
for r in rows:
    m,conv,est=form(r['ga'])
    C['544 stated']+=bool(m); C['544 convert']+=bool(conv); C['544 estimate']+=est
    if m: C['544 stated unit '+m.group(2)]+=1
    if conv: C['544 convert '+r['u']]+=1
    m2,conv2,est2=form(r['gb'])
    C['m200 stated']+=bool(m2); C['m200 convert']+=bool(conv2); C['m200 estimate']+=est2
for k in sorted(C): print(k,C[k])
# trace form templates at m200
T=collections.Counter(re.sub(r'find the [^\.\n]+','find the X',re.sub(r'in (feet|inches|meters|centimeters)','in U',r['gb'].split('</think>')[0])) for r in rows)
print('m200 distinct trace templates',len(T))
for t,c in T.most_common(6): print(c,repr(t))
T=collections.Counter(re.sub(r'\(first seen[^\)]*\)','(first seen ..)',re.sub(r'is [\d\.]+ ?[a-z]+','is N U',re.sub(r'find the [^\(\n]+','find the X ',r['ga'].split('</think>')[0]))) for r in rows)
print('544 distinct trace templates',len(T))
for t,c in T.most_common(8): print(c,repr(t[:300]))
