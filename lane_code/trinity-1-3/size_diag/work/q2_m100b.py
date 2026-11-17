import json, math, collections, random, re
from load import load, P544, num, mra, unit
from q2c_lib import slip
P100='/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/af35386aa3e/fetched/x/main/a0/results/budget_2048/0/items_a0.jsonl'
I100='/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/af35386aa3e/fetched/x/ITEMS.jsonl'
rows=json.load(open('size_rows_544_m200_slip.json'))
m=load(P100,{'object_size_estimation'})
# cross-check the m100 per-item scores against the return's ITEMS.jsonl
I=load(I100,{'object_size_estimation'}) 
mism=sum(1 for r in rows if r['id'] in I and abs(I[r['id']]['score']-m[r['id']]['score'])>1e-9); print('ITEMS.jsonl rows matched',sum(1 for r in rows if r['id'] in I),'score mismatches',mism)
for r in rows:
    d=m[r['id']]; p=num(d['extracted_answer']); r['pc']=p; r['sc']=d['score']
    v,p2=slip(p,r['g'],r['u']); r['slipc']=v; r['fixc']=mra(p2,r['g']); r['gc']=d['raw_generation']
def boot(fa,fb,R,B=10000,seed=20261115):
    by=collections.defaultdict(list)
    for x in R: by[x['room']].append(fb(x)-fa(x))
    rooms=list(by); rnd=random.Random(seed); v=[]
    for _ in range(B):
        s=c=0
        for _ in rooms:
            y=by[rnd.choice(rooms)]; s+=sum(y); c+=len(y)
        v.append(100*s/c)
    v.sort(); d=100*sum(sum(y) for y in by.values())/len(R)
    return '%+.2f [%.2f, %.2f]'%(d,v[int(.025*B)],v[int(.975*B)-1])
n=len(rows)
for lab,s,f,sl in (('544','sa','fixa','slipa'),('m100','sc','fixc','slipc'),('m200','sb','fixb','slipb')):
    print('%-5s MRA %.2f  slips-reinterpreted %.2f  slips %d'%(lab,100*sum(r[s] for r in rows)/n,100*sum(r[f] for r in rows)/n,sum(1 for r in rows if r[sl])))
print('m100-544 raw',boot(lambda r:r['sa'],lambda r:r['sc'],rows),'| both reinterpreted',boot(lambda r:r['fixa'],lambda r:r['fixc'],rows))
print('m200-m100 raw',boot(lambda r:r['sc'],lambda r:r['sb'],rows),'| both reinterpreted',boot(lambda r:r['fixc'],lambda r:r['fixb'],rows))
for grp,us in (('metric',('cm','m')),('imperial',('in','ft'))):
    R=[r for r in rows if r['u'] in us]
    print(grp,len(R),'m100-544 raw',boot(lambda r:r['sa'],lambda r:r['sc'],R),'reint',boot(lambda r:r['fixa'],lambda r:r['fixc'],R),'| m200-544 raw',boot(lambda r:r['sa'],lambda r:r['sb'],R),'reint',boot(lambda r:r['fixa'],lambda r:r['fixb'],R))
for u in ('cm','m','in','ft'):
    R=[r for r in rows if r['u']==u]
    print('  %-2s n=%2d  544 %.1f  m100 %.1f  m200 %.1f | slips 544/m100/m200 %d/%d/%d'%(u,len(R),100*sum(r['sa'] for r in R)/len(R),100*sum(r['sc'] for r in R)/len(R),100*sum(r['sb'] for r in R)/len(R),sum(1 for r in R if r['slipa']),sum(1 for r in R if r['slipc']),sum(1 for r in R if r['slipb'])))
ok=[r for r in rows if not r['slipa'] and not r['slipc'] and not r['slipb']]
import statistics as st
w=lambda key: sum(1 for r in ok if abs(math.log(r[key]/r['g']))<math.log(1.1))/len(ok)
print('items no slip at any export',len(ok),'within 10%%: 544 %.3f m100 %.3f m200 %.3f'%(w('pa'),w('pc'),w('pb')))
print('templates m100: D0 form',sum(1 for r in rows if 'from the frames' in r['gc'].split('</think>')[0]),'stated',sum(1 for r in rows if 'longest edge is' in r['gc']))
json.dump(rows,open('size_rows_544_m100_m200.json','w'))
