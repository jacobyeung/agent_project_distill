import sqlite3,json,re
from collections import Counter
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
P={'nearest-to-farthest':re.compile(r'ordered nearest to farthest'),'asks for the closest':re.compile(r'asks for the closest'),
   'X is shorter/longer than Y':re.compile(r' is (shorter|longer) than '),'order them from shortest/smallest':re.compile(r'order them from (shortest|smallest|longest|largest)'),
   'longest edge of':re.compile(r'longest edge of'),'compare their':re.compile(r'compare their')}
C=Counter(); N=Counter()
for i,row,t in c.execute('select i,row,target from rows'):
    m=re.search(r'"category":"([^"]+)"',row); cat=m.group(1) if m else '?'
    j=row.find('"target":'); tg=row[j:j+3000] if j>=0 else ''
    N[cat]+=1
    for k,p in P.items():
        if p.search(tg): C[(k,cat)]+=1
for k in P:
    print(k, [(cat,n) for (kk,cat),n in C.most_common() if kk==k][:6])
print('rel size rows', {k:v for k,v in N.items() if 'size' in k})
