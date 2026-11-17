import json,collections,re,numpy as np
RP=[json.loads(l) for l in open('replay_out.jsonl')]
print('errors',sum('error' in r for r in RP), collections.Counter(r.get('error','')[:80] for r in RP if 'error' in r).most_common(3))
P=json.load(open('pairs_cache.json')); H={(o['id'],o['name']):o for o in P}
n2r=json.load(open('n2r_calls.json'))['unflagged']
T=collections.defaultdict(set)
for key,r in n2r.items():
    for c in r['calls']:
        if c['kind']=='ground' and c['st'] in ('seen','not seen'): T[(key,c['name'])].add(c['st'])
st=lambda resp: 'not seen' if resp.strip().endswith(': not seen') else ('seen' if ': frames' in resp else 'other:'+resp[:30])
rep=collections.defaultdict(dict)
for r in RP:
    if 'error' in r: continue
    for n,resp in r['ground'].items(): rep[(r['id'],n)][(r['geo'],r['rule'])]=st(resp)
for arm in (('tower','null_argmax'),('hybrid','null_argmax'),('tower','candidates_argmax'),('hybrid','candidates_argmax')):
    C=collections.Counter(); A=collections.Counter()
    for k,v in rep.items():
        if arm not in v or k not in H: continue
        C[v[arm]]+=1; A[(H[k]['h1'],v[arm])]+=1
    print(arm,dict(C),'vs H1-0 own:',dict(A))
# tower replay vs 170056 tower arm and vs parity
B=collections.Counter()
for k,v in rep.items():
    if ('tower','null_argmax') in v and k in H:
        t=T.get(k); t=next(iter(t)) if t else 'nc'; B[(t,v[('tower','null_argmax')])]+=1
print('170056 tower arm vs replay tower+selector(null):',dict(B))
# stage-D not-seen pairs under hybrid null: agreement
D=[k for k in rep if k in H and H[k]['h1']=='not seen']
print('H1-0 ns pairs replayed',len(D), collections.Counter((H[k]['cls'][0],rep[k].get(('hybrid','null_argmax')),rep[k].get(('tower','null_argmax'))) for k in D))
json.dump({'%s|%s'%k:{'%s/%s'%a:s for a,s in v.items()} for k,v in rep.items()},open('replay_status.json','w'))
