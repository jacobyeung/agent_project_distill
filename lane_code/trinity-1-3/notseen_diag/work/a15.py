import json,collections,re,numpy as np
P=json.load(open('pairs_cache.json'))
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
n2r=json.load(open('n2r_calls.json'))['unflagged']
T=collections.defaultdict(set)
for key,r in n2r.items():
    for c in r['calls']:
        if c['kind']=='ground' and c['st'] in ('seen','not seen'): T[(key,c['name'])].add(c['st'])
for o in P:
    t=T.get((o['id'],o['name'])); o['tower']=next(iter(t)) if t else 'nc'; o['room']=I[o['id']]['room_key']
rooms=sorted(set(o['room'] for o in P)); byr=collections.defaultdict(list)
for o in P: byr[o['room']].append(o)
rng=np.random.default_rng(20261115)
def boot(stat,n=10000):
    v=[]
    for _ in range(n):
        pick=rng.choice(len(rooms),len(rooms)); S=[o for i in pick for o in byr[rooms[i]]]
        v.append(stat(S))
    v=np.array([x for x in v if x is not None and np.isfinite(x)]); return np.percentile(v,[2.5,97.5])
own=lambda S:np.mean([o['h1']=='not seen' for o in S])
tow=lambda S:np.mean([o['tower']=='not seen' for o in S if o['tower']!='nc'])
diff=lambda S:np.mean([(o['h1']=='not seen')-(o['tower']=='not seen') for o in S if o['tower']!='nc'])
print('rooms',len(rooms),'pairs',len(P))
print('own ns rate',round(own(P),3),boot(own).round(3))
print('tower ns rate',round(tow(P),3),boot(tow).round(3))
print('own-tower',round(diff(P),3),boot(diff).round(3))
def grp(f,a,b):
    def s(S):
        A=[o for o in S if f(o)==a]; B=[o for o in S if f(o)==b]
        if not A or not B: return None
        return np.mean([o['h1']=='not seen' for o in A])-np.mean([o['h1']=='not seen' for o in B])
    return s
ds=lambda o:o['dataset']
print('scannetpp - others', round(grp(lambda o:'pp' if o['dataset']=='scannetppv2' else 'o','pp','o')(P),3), boot(grp(lambda o:'pp' if o['dataset']=='scannetppv2' else 'o','pp','o')).round(3))
print('portrait - landscape', round(grp(lambda o:o['portrait'] if 'portrait' in o else None,True,False)(P) or 0,3))
