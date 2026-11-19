import sqlite3,json
from collections import Counter
c=sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro',uri=True)
a=Counter()
for i,row in c.execute('select i,row from rows'):
    if 'direction' in row:
        if '"category":"object_rel_direction' in row[:300]: a['prefix']+=1
        else:
            d=json.loads(row); a[(d.get('category'),d.get('pool'))]+=1
print(a.most_common(20))
