import json,collections,numpy as np
P=json.load(open('pairs_cache.json'))
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
MC='n2r/mc/sj/mask_recall_run/results/'
man={c['native']:c for c in json.load(open(MC+'dense/MANIFEST.json'))['captures']}
for o in P: o['portrait']=man[o['native']]['hw'][0]>man[o['native']]['hw'][1]; o['room']=I[o['id']]['room_key']
rng=np.random.default_rng(20261115)
def bootr(units,stat,n=10000):
    rooms=sorted(set(u['room'] for u in units)); byr=collections.defaultdict(list)
    for u in units: byr[u['room']].append(u)
    v=[]
    for _ in range(n):
        pick=rng.choice(len(rooms),len(rooms)); S=[u for i in pick for u in byr[rooms[i]]]
        x=stat(S)
        if x is not None: v.append(x)
    return np.percentile(v,[2.5,97.5]).round(3)
def pdiff(S):
    A=[o for o in S if o['portrait']]; B=[o for o in S if not o['portrait']]
    if not A or not B: return None
    return np.mean([o['h1']=='not seen' for o in A])-np.mean([o['h1']=='not seen' for o in B])
print('portrait-landscape',round(pdiff(P),3),bootr(P,pdiff))
ark=[o for o in P if o['dataset']=='arkitscenes']; print('arkit pairs',len(ark),'portrait',sum(o['portrait'] for o in ark))
print('arkit portrait-landscape',round(pdiff(ark),3) if pdiff(ark) is not None else None)
# read-level projected gains
R=[json.loads(l) for l in open('f3/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl')]
C=json.load(open('conv.json')); conv=set(C['conv']); rest=set(C['rest'])
U=[]
for x in R:
    if x['mode']!='none': continue
    U.append(dict(room=x['room_key'],s=x['measurements']['M2']['task_accuracy'],conv=x['id'] in conv,ns=(x['id'] in conv or x['id'] in rest),cap=x['output']['finish']=='max_calls'))
def ga(S):
    cl=[u['s'] for u in S if not u['ns']]
    if not cl: return None
    m=np.mean(cl); return 100*sum((m-u['s']) for u in S if u['conv'])/len(S)
def gc(S):
    an=[u['s'] for u in S if u['ns'] and not u['cap']]
    if not an: return None
    m=np.mean(an); return 100*sum(m for u in S if u['cap'])/len(S)
print('(a) drop-null gain',round(ga(U),1),bootr(U,ga)); print('(c) recovery gain',round(gc(U),1),bootr(U,gc))
