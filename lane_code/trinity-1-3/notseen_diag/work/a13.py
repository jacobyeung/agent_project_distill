import json,collections,re,numpy as np
R=[json.loads(l) for l in open('f3/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl')]
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
P=json.load(open('pairs_cache.json'))
cls={(o['id'],o['name']):o['cls'] for o in P}
base=[x for x in R if x['mode']=='none']
def nsnames(x):
    out=set()
    for c in x['output']['calls']['records']:
        if c['family']=='ground' and c.get('served') and 'not seen' in (c.get('response') or ''):
            out.add(re.search(r'obj="([^"]*)"',c['call'])[1])
    return out
clean=[x for x in base if not nsnames(x)]; ns=[x for x in base if nsnames(x)]
sc=lambda x:x['measurements']['M2']['task_accuracy']
def unit(q):
    q=q.lower()
    for u,k in (('centimet','cm'),('feet','ft'),('foot','ft'),('inch','in'),('meter','m'),('metre','m')):
        if u in q: return k
    return '?'
print('clean reads',len(clean),'MRA',round(np.mean([sc(x) for x in clean]),3),'metre-q clean',round(np.mean([sc(x) for x in clean if unit(I[x['id']]['question'])=='m']),3), sum(unit(I[x['id']]['question'])=='m' for x in clean))
conv=[x for x in ns if all(cls.get((x['id'],n))=='D_has_eligible_raster' for n in nsnames(x))]
rest=[x for x in ns if x not in conv]
print('not-seen reads',len(ns),'convertible by (a) (all ns names class D):',len(conv),'remaining',len(rest))
cur=sum(sc(x) for x in conv); print('current score sum convertible',round(cur,2),'capped among convertible',sum(x['output']['finish']=='max_calls' for x in conv))
m_clean=np.mean([sc(x) for x in clean])
# bootstrap over rooms for clean-read MRA used as the converted-read expectation
rng=np.random.default_rng(20261115)
rooms=sorted(set(x['room_key'] for x in clean)); byr=collections.defaultdict(list)
for x in clean: byr[x['room_key']].append(sc(x))
bs=[]
for _ in range(10000):
    pick=rng.choice(len(rooms),len(rooms)); v=[s for i in pick for s in byr[rooms[i]]]; bs.append(np.mean(v))
lo,hi=np.percentile(bs,[2.5,97.5]); print('clean MRA',round(m_clean,3),'CI',round(lo,3),round(hi,3))
gain=(len(conv)*m_clean-cur)/150; print('est gain (a) MRA pts',round(100*gain,1),'range',round(100*(len(conv)*lo-cur)/150,1),round(100*(len(conv)*hi-cur)/150,1))
# capped-read share remaining after (a)
print('remaining reads capped',sum(x['output']['finish']=='max_calls' for x in rest),'of',len(rest))
json.dump(dict(conv=[x['id'] for x in conv],rest=[x['id'] for x in rest]),open('conv.json','w'))
