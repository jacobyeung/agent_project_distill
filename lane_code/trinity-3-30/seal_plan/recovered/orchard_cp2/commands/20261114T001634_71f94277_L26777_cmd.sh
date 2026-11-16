<!-- recovered by seal_plan: transcript=71f94277 line=26777 utc=2026-11-14T00:16:34.419Z kind=commands original_path=(bash command)  -->
F=/scratch/jjyeung/orch_cd/orchard_cp2/out/STATE_COPY_CHEAP_169097_b9bfe98f/memory_scope_failure.json; wc -c $F; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json
v=json.load(open('$F'))
def walk(x,p='',d=0):
    if isinstance(x,dict):
        for k,val in x.items(): walk(val,p+'/'+k,d+1)
    elif isinstance(x,list):
        if len(x)>6 and all(not isinstance(i,(dict,list)) for i in x): print(p[:110], str(x[:6])[:160],'... n=',len(x))
        else:
            for i,val in enumerate(x[:4]): walk(val,p+'/'+str(i),d+1)
            if len(x)>4: print(p[:110],'... n=',len(x))
    else: print(p[:110], str(x)[:200])
walk(v)
" | head -n 90