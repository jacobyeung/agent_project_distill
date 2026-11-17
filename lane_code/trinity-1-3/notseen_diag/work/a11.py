import json,collections,ast,numpy as np
P=json.load(open('pairs_cache.json'))
MC='n2r/mc/sj/mask_recall_run/results/'
man={c['native']:c for c in json.load(open(MC+'dense/MANIFEST.json'))['captures']}
cache={}
def load(native):
    if native not in cache:
        c=man[native]; cache[native]=json.loads(np.load(MC+'dense/candidates/'+c['scene'].replace('/','__')+'.npz')['payload'].tobytes())
    return cache[native]
seen=set(); sample=[]
order=['heater','computer mouse','blanket','bucket','nightstand','shoes','power strip','keyboard','headphones','dishwasher','paper bag','shoe rack','radiator','slippers']
for nm in order:
    for o in P:
        if o['h1']!='not seen' or o['name']!=nm or (o['native'],nm) in seen: continue
        seen.add((o['native'],nm))
        c=load(o['native']); ph=o['dense'].get('phrase',nm)
        best=None
        for s in range(32):
            rec=c['frames'][str(s)]['phrases'].get(ph) if o['dense']['cache']=='ok' else None
            if rec is None: continue
            for e in rec.get('instances') or []:
                sc=float(e['score'])
                if best is None or sc>best[0]: best=(sc,s,e.get('box'),rec.get('presence'))
        if best is None:
            # pick frame with max presence
            s=0; best=(0,s,None,None)
        fr=man[o['native']]['frames'][best[1]]
        sample.append(dict(id=o['id'],name=nm,native=o['native'],cls=o['cls'],slot=best[1],score=best[0],box=best[2],presence=best[3],png=fr['path'],sha=fr['sha256']))
        break
print(json.dumps(sample,indent=0)[:4000]); json.dump(sample,open('vis_sample.json','w'))
print(len(sample))
