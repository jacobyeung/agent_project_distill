import json,collections,re
rows=json.load(open('calls.json'))
n2r=json.load(open('n2r_calls.json'))['unflagged']
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
# H1-0 per (id,mode,name) status: seen if any ground call for that name was seen, else not seen
H=collections.defaultdict(set)
for r in rows:
    if r['family']=='ground' and r['st'] in ('seen','not seen'):
        H[(r['id'],r['mode'],r['name'])].add(r['st'])
def hst(k):
    s=H.get(k)
    if not s: return None
    assert len(s)==1, (k,s)
    return next(iter(s))
T=collections.defaultdict(set)
for key,r in n2r.items():
    for c in r['calls']:
        if c['kind']=='ground' and c['st'] in ('seen','not seen'): T[(key,c['name'])].add(c['st'])
# baseline pairs
pairs=sorted(set((i,n) for (i,m,n) in H if m=='none'))
tab=collections.Counter()
names_ns=[]
for i,n in pairs:
    h=hst((i,'none',n)); t=T.get((i,n)); t=next(iter(t)) if t and len(t)==1 else ('mixed' if t else 'not_called')
    tab[(h,t)]+=1
print('unique (item,name) pairs baseline:',len(pairs))
for k,v in sorted(tab.items()): print(k,v)
ns=[(i,n) for i,n in pairs if hst((i,'none',n))=='not seen']
print('H1-0 baseline not-seen (item,name):',len(ns),'items',len(set(i for i,n in ns)))
# per-mode flips
for m in ('scale_scene:0.5','scale_scene:2'):
    c=collections.Counter()
    for i,n in pairs:
        b=hst((i,'none',n)); p=hst((i,m,n))
        if p is None: continue
        c[(b,p)]+=1
    print(m,dict(c))
json.dump(dict(ns=ns),open('ns_pairs.json','w'))
