import json, math, collections, random, re, sys, os, glob
from load import load, P544, num, mra, unit
from q2c_lib import slip
B='/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/af35386aa3e/fetched/x'
c=sorted(glob.glob(B+'/main/a0/results/budget_2048/0/items_a0.jsonl'))
if not c: print('m100 main items not found'); sys.exit(3)
P100=c[0]; print('m100 file',P100)
T={'object_size_estimation','relative_size_object'}
a=load(P544,T); m=load(P100,T)
ids=[k for k in a if a[k]['question_type']=='object_size_estimation']
missing=[k for k in a if k not in m]; print('items missing at m100',len(missing))
def boot(pairs,B=10000,seed=20261115):
    by=collections.defaultdict(list)
    for room,d in pairs: by[room].append(d)
    rooms=list(by); rnd=random.Random(seed); v=[]
    for _ in range(B):
        s=n=0
        for _ in rooms:
            x=by[rnd.choice(rooms)]; s+=sum(x); n+=len(x)
        v.append(100*s/n)
    v.sort(); d=100*sum(sum(x) for x in by.values())/sum(len(x) for x in by.values()); return d,v[int(.025*B)],v[int(.975*B)-1]
pairs=[(a[k]['room'],m[k]['score']-a[k]['score']) for k in ids]
print('object size m100 MRA %.2f vs 544 %.2f, paired %+.2f [%.2f, %.2f] (n=%d)'%((100*sum(m[k]['score'] for k in ids)/len(ids),100*sum(a[k]['score'] for k in ids)/len(ids))+boot(pairs)+(len(ids),)))
d0=sum(1 for k in ids if 'I estimate it from the frames' in m[k]['raw_generation'] or 'from the frames.' in m[k]['raw_generation'].split('</think>')[0] and 'longest edge is' not in m[k]['raw_generation'])
sealed=sum(1 for k in ids if re.search(r'longest edge is [\d\.]+',m[k]['raw_generation']))
print('m100 size traces: D0 template',d0,'stated length (544 form)',sealed,'of',len(ids))
fix=[]; sl=collections.Counter()
for k in ids:
    g=num(a[k]['ground_truth']); p=num(m[k]['extracted_answer']); u=unit(a[k]['question'])
    v,p2=slip(p,g,u) if p else (None,p)
    if v: sl[(u,v)]+=1
    fix.append((a[k]['room'],(mra(p2,g) if p else 0)-a[k]['score']))
print('m100 unit slips',sum(sl.values()),dict(sl))
rs=[k for k in a if a[k]['question_type']=='relative_size_object']
numans=sum(1 for k in rs if re.fullmatch(r'\s*-?\d+(\.\d+)?\s*',str(m[k]['extracted_answer'] or '')))
pairs=[(a[k]['room'],m[k]['score']-a[k]['score']) for k in rs]
print('relative size m100 %.2f vs 544 %.2f paired %+.2f [%.2f, %.2f]; numeric answers %d of %d'%((100*sum(m[k]['score'] for k in rs)/len(rs),100*sum(a[k]['score'] for k in rs)/len(rs))+boot(pairs)+(numans,len(rs))))
# extra: slip-fixed and metric-only deltas; relative count hijack
fixd=boot(fix)
print('object size m100 slips reinterpreted: %+.2f [%.2f, %.2f]'%fixd)
met=[(a[k]['room'],m[k]['score']-a[k]['score']) for k in ids if unit(a[k]['question']) in ('cm','m')]
print('metric items m100 %+.2f [%.2f, %.2f] n=%d'%(boot(met)+(len(met),)))
rc=load(P544,{'relative_count'}); mc=load(P100,{'relative_count'})
nn=sum(1 for k in mc if re.fullmatch(r'\s*-?\d+(\.\d+)?\s*',str(mc[k]['extracted_answer'] or '')))
print('relative count m100 numeric answers',nn,'of',len(mc),'score %.1f'%(100*sum(mc[k]['score'] for k in mc)/len(mc)))
json.dump({k:dict(pred=m[k]['extracted_answer'],score=m[k]['score'],gen=m[k]['raw_generation']) for k in ids},open('m100_size_items.json','w'))
