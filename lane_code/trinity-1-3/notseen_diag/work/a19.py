import json,collections,re,numpy as np
RP=[json.loads(l) for l in open('replay_out.jsonl')]
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
U={'m':1.,'cm':.01,'ft':.3048,'in':.0254}
def unit(q):
    q=q.lower()
    for u,k in (('centimet','cm'),('feet','ft'),('foot','ft'),('inch','in'),('meter','m'),('metre','m')):
        if u in q: return k
def mra(p,g):
    th=np.arange(.5,.96,.05); return float(np.mean([abs(p-g)/g < 1-t for t in th]))
R={}
for r in RP:
    if 'error' in r: continue
    R[(r['id'],r['geo'],r['rule'])]=r
rows=[]
for (i,g,rule),r in R.items():
    if rule!='null_argmax': continue
    a=R.get((i,g,'candidates_argmax'))
    it=I[i]; u=unit(it['question']); gt=float(it['ground_truth'])*U[u]
    def val(x):
        m=re.match(r'distance ([\d\.]+) m',(x or {}).get('gap') or '')
        return float(m[1]) if m else None
    v0,v1=val(r),val(a)
    ns0=any(s.strip().endswith('not seen') for s in r['ground'].values())
    rows.append(dict(id=i,geo=g,u=u,gt=gt,clean=not ns0,v0=v0,v1=v1,room=it['room_key']))
for g in ('tower','hybrid'):
    S=[x for x in rows if x['geo']==g]
    cl=[x for x in S if x['clean'] and x['v0'] is not None]; rs=[x for x in S if not x['clean'] and x['v1'] is not None]
    rel=lambda X,k:np.median([abs(x[k]-x['gt'])/x['gt'] for x in X])
    print(g,'reads',len(S),'clean with gap',len(cl),'rescued by (a\') with gap',len(rs),'still no gap',sum(1 for x in S if not x['clean'] and x['v1'] is None))
    print('  clean: median |err| m %.2f rel %.2f program-MRA %.3f'%(np.median([abs(x['v0']-x['gt']) for x in cl]),rel(cl,'v0'),np.mean([mra(x['v0'],x['gt']) for x in cl])))
    print('  rescued: median |err| m %.2f rel %.2f program-MRA %.3f'%(np.median([abs(x['v1']-x['gt']) for x in rs]),rel(rs,'v1'),np.mean([mra(x['v1'],x['gt']) for x in rs])))
    allp=[mra(x['v1'],x['gt']) if x['v1'] is not None else 0 for x in S]; nullp=[mra(x['v0'],x['gt']) if x['v0'] is not None else 0 for x in S]
    print('  program-MRA over all replayed reads (no-gap = 0): null %.3f  (a\') %.3f  diff %+.1f pts'%(np.mean(nullp),np.mean(allp),100*(np.mean(allp)-np.mean(nullp))))
json.dump(rows,open('replay_gaps.json','w'))
