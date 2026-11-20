W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work
for d in tt24t2 cps24t1; do ls -la $W/$d | head -30; echo "@@@ $d/RESULT.json $(stat -c %s $W/$d/RESULT.json) $(sha256sum < $W/$d/RESULT.json | cut -c1-64)"; done
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'P'
import json
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w/work'
for d in ('tt24t2','cps24t1'):
    v=json.load(open(f'{W}/{d}/RESULT.json'))
    print('=====',d,list(v) if isinstance(v,dict) else type(v))
    for k,x in v.items():
        s=json.dumps(x)
        print('--',k,len(s)); print(s[:1800])
P
