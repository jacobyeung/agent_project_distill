<!-- recovered by seal_plan: transcript=71f94277 line=31798 utc=2026-11-14T14:24:31.692Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/evalx/work/milestone/s23/ifp0_aded62aed7218d81a; ls -t $D | head -n 5; F=$(ls -t $D/OBSERVATION_*.json | head -n 1); echo $F; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - "$F" <<'EOF'
import json,sys
d=json.load(open(sys.argv[1]))
def find(o,keys,path='',out=None):
    out=[] if out is None else out
    if isinstance(o,dict):
        for k,v in o.items():
            if k in keys: out.append((path+'/'+k, v))
            find(v,keys,path+'/'+k,out)
    elif isinstance(o,list):
        for i,v in enumerate(o[:50]): find(v,keys,path+'/'+str(i),out)
    return out
print(list(d.keys())[:30])
for p,v in find(d,{'phases','latest_phase','phase','steps','training','state','elapsed','step','last_step','checked_utc'}):
    print(p[:80], str(v)[:700])
EOF