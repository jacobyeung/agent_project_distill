import json,sqlite3,collections,numpy as np,re
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/rows.sqlite?mode=ro',uri=True)
rows=[json.loads(t) for (t,) in db.execute('select row from rows order by i')]
L={}
for r in rows:
    p=r['provenance']['raster']
    if p not in L:
        with np.load(p) as z:L[p]=[' '.join(str(x).lower().replace('_',' ').split()) for x in z['labels']]
use=collections.Counter(o['label'] for r in rows for o in r['provenance']['instances'])
print('distinct labels',len(use));print(use.most_common(80))
SYN=[{'trash can','trash bin','garbage bin','wastebasket','trashcan','bin','recycling bin','waste bin'},{'sofa','couch'},{'tv','television'},{'cabinet','cupboard','cabinets','kitchen cabinet','kitchen cabinets'},{'shelf','shelves','bookshelf','bookshelves','shelving'},{'rug','carpet','mat'},{'nightstand','night stand','bedside table'},{'monitor','computer monitor','screen'},{'door','doors','doorframe','door frame'},{'window','windows','windowsill'},{'lamp','light','ceiling light','ceiling lamp','table lamp'},{'refrigerator','fridge'},{'desk','table'},{'chair','office chair','armchair','stool'}]
def head(l):return l.split()[-1]
issues=collections.Counter();ex=collections.defaultdict(list);rowbad=collections.Counter()
for r in rows:
    labs=L[r['provenance']['raster']];bad=False
    for o in r['provenance']['instances']:
        a=o['label']
        for b in set(labs):
            if b==a:continue
            kinds=[]
            if b.startswith(a+' ') or a.startswith(b+' '):kinds.append('prefix')
            if head(a)==head(b):kinds.append('samehead')
            if head(a).rstrip('s')==head(b).rstrip('s') and head(a)!=head(b):kinds.append('plural-head')
            if any(a in s and b in s for s in SYN):kinds.append('synonym')
            for k in kinds:
                issues[k]+=1;bad=True
                if len(ex[k])<25:ex[k].append((r['question_type'],a,b))
    rowbad[(r['question_type'],bad)]+=1
print(issues)
for k,v in ex.items():print(k,collections.Counter((a,b) for _,a,b in v).most_common(25))
print(sorted(rowbad.items()))
# synonym among the row's own objects
own=collections.Counter()
for r in rows:
    labs=[o['label'] for o in r['provenance']['instances']]
    for i,a in enumerate(labs):
        for b in labs[i+1:]:
            if any(a in s and b in s for s in SYN) or head(a)==head(b) or b.startswith(a+' ') or a.startswith(b+' '):own[(r['question_type'],a,b)]+=1
print('within-row sibling/synonym pairs',sum(own.values()),own.most_common(20))
json.dump({k:v for k,v in L.items()},open('labels.json','w'))
