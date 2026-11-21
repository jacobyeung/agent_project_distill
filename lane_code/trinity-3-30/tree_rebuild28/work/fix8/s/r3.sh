W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
cd $W
ls w24z12/out | grep -i upload
for f in w24z12/out/UPLOADS_24M4Z12.json w24z12/out/UPLOADS_24M4Z12_GO.json; do [ -f $f ] && python3 -c "
import json,sys,collections
v=json.load(open('$f')); rows=v.get('files',v.get('rows',[]))
print('$f',len(rows))
d=collections.Counter()
for r in rows:
    lp=r.get('local_path','')
    d['/'.join(lp.split('/')[:9])]+=1
    if any(x in r.get('name','') for x in ('e3ee51da','8957d119','93b21a3a','ca0616db','0d28fdd4','f41d15aa')): print('  ',r.get('name'),lp)
for k,c in d.most_common(15): print(c,k)
"; done
ls -d w18/work/build18/inputs 2>/dev/null && ls w18/work/build18/inputs | head -30
ls w12/work/n1fix2/inputs 2>/dev/null | head
ls ext inputs mirror | head -40
