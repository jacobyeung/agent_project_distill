K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28fix/n_go; C=/scratch/jjyeung/orch_n30/n_review/r1j/t/student_pilot
n=$(grep -n "^def division_admits" $C/carrier_c1_run.py < /dev/null | cut -d: -f1); echo "== division_admits at $n"; sed -n "${n},$((n+30))p" $C/carrier_c1_run.py < /dev/null
grep -n "division_admits" $C/*.py < /dev/null | head
echo "== k files"; ls -la $K/k < /dev/null; grep -l '"streams"' $K/k/*.json < /dev/null
for f in $K/k/*.json; do python3 -c "
import json,sys
d=json.load(open('$f'))
def walk(d,p):
    if isinstance(d,dict):
        for k,v in d.items():
            if k in ('streams','division','preservation','pointing','routing') : print('$f'.split('/')[-1],p+'/'+k,json.dumps(v)[:400])
            walk(v,p+'/'+k)
    elif isinstance(d,list):
        for i,v in enumerate(d[:50]): walk(v,p+'[%d]'%i)
walk(d,'')
" < /dev/null; done 2>&1 | head -40
