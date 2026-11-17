import json,collections,re,numpy as np
R1=[json.loads(l) for l in open('replay_out.jsonl')]; R2=[json.loads(l) for l in open('replay_out2.jsonl')]
k=lambda r:(r['id'],r['geo'],r['rule'])
A={k(r):r for r in R1 if 'error' not in r}; B={k(r):r for r in R2 if 'error' not in r}
same=sum(A[x]['ground']==B[x]['ground'] and A[x]['gap']==B[x]['gap'] for x in A if x in B); print('replay1 vs replay2 identical on',same,'of',sum(x in B for x in A))
I={x['id']:x for x in json.load(open('f3/p446/items/devs1_routed.json'))['items']}
P=json.load(open('pairs_cache.json')); H={(o['id'],o['name']):o for o in P}
n2r=json.load(open('n2r_calls.json'))['unflagged']
T=collections.defaultdict(set)
for key,r in n2r.items():
    for c in r['calls']:
        if c['kind']=='ground' and c['st'] in ('seen','not seen'): T[(key,c['name'])].add(c['st'])
st=lambda s: 'not seen' if s.strip().endswith(': not seen') else 'seen'
rep=collections.defaultdict(dict); emp={}
for r in B.values():
    q={x['name']:x['candidates'] for x in r['queries']}
    for n,s in r['ground'].items():
        rep[(r['id'],n)][(r['geo'],r['rule'])]=st(s)
        if r['rule']=='null_argmax': emp[(r['id'],n,r['geo'])]=q.get(n,0)==0
keys=[x for x in rep if x in H and len(rep[x])==4]
print('pairs replayed',len(keys),'items',len(set(x[0] for x in keys)))
one=lambda s:next(iter(s)) if s else 'nc'
row=collections.Counter()
for x in keys:
    row['tower170056_ns']+=one(T.get(x))=='not seen'
    row['sel_G3T_ns']+=rep[x][('tower','null_argmax')]=='not seen'
    row['sel_ownpose_G3Tdepth_ns']+=rep[x][('hybrid','null_argmax')]=='not seen'
    row['H1-0_own_ns']+=H[x]['h1']=='not seen'
    row['aprime_G3T_ns']+=rep[x][('tower','candidates_argmax')]=='not seen'
    row['aprime_hybrid_ns']+=rep[x][('hybrid','candidates_argmax')]=='not seen'
    row['empty_cands_G3T']+=emp[(x[0],x[1],'tower')]; row['empty_cands_hybrid']+=emp[(x[0],x[1],'hybrid')]
print(dict(row))
agree=sum((rep[x][('hybrid','null_argmax')]=='not seen')==(H[x]['h1']=='not seen') for x in keys); print('hybrid vs H1-0 agreement',agree,'/',len(keys))
cm=collections.Counter((H[x]['h1'],rep[x][('hybrid','null_argmax')]) for x in keys); print('H1-0 x hybrid',dict(cm))
ct=collections.Counter((H[x]['h1'],rep[x][('tower','null_argmax')]) for x in keys); print('H1-0 x sel_G3T',dict(ct))
cls=collections.Counter((H[x]['cls'][0],rep[x][('hybrid','null_argmax')],rep[x][('tower','null_argmax')]) for x in keys if H[x]['h1']=='not seen'); print('H1-0 ns by class x (hybrid,G3T):',dict(cls))
# per dataset (hybrid null)
D=collections.Counter((H[x]['dataset'],rep[x][('hybrid','null_argmax')]) for x in keys); print('hybrid by dataset',dict(D))
json.dump({'%s|%s'%x:{'%s/%s'%a:s for a,s in rep[x].items()} for x in keys},open('replay_status.json','w'))
