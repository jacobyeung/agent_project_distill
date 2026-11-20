D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173864/173864; date -u +%TZ; cd $D; cat timings.json | head -c 1500; echo; tail -5 job.log | cut -c1-300
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
def short(d,depth=0,pre=''):
    for k,v in d.items():
        if isinstance(v,dict) and depth<2: print(pre+k+':'); short(v,depth+1,pre+'  ')
        else:
            s=json.dumps(v); print(pre+k+' = '+(s[:220]))
for f in ('nd.json','chain.json','routing_types.json','proc_check.json'):
    print('=====',f); d=json.load(open(f)); short(d) if isinstance(d,dict) else print(str(d)[:500])
PY
