import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
a=K.facing('S1',544,'forward'); b=K.facing('R1',200,'forward'); c=K.facing('R1',400,'forward')
mb={r['id']:r for r in b}; mc={r['id']:r for r in c}
print(len(a),len(b),len(c)); print(sorted(a[0].keys()))
n=0
for r in a:
    z=mc[r['id']]
    if z['score']==0 and z['type'].endswith('hard'):
        n+=1
        if n>2: break
        print('=====',r['id'],r['type'],r['gt'],r['question'][:400],r['options'])
        for x in (r,mb[r['id']],z):
            print('--- step',x['step'],'pred',x['pred'],'score',x['score'],'fc',x['forced_close'],'tt',x['think_tokens'])
            print((x['text'] or '')[:2500])
