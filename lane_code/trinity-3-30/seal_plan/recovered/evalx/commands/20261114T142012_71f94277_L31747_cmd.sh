<!-- recovered by seal_plan: transcript=71f94277 line=31747 utc=2026-11-14T14:20:12.345Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/evalx/work/milestone/native_probe_s23_01/pilot3_failure; ls $D | head -n 20; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json,glob,os
D='/scratch/jjyeung/orch_cd/evalx/work/milestone/native_probe_s23_01/pilot3_failure'
r=json.load(open(D+'/FAILURE_REPORT.json'))
print(list(r.keys())[:40])
def find(o,key,path=''):
    if isinstance(o,dict):
        for k,v in o.items():
            if k==key: yield path+'/'+k,v
            yield from find(v,key,path+'/'+k)
    elif isinstance(o,list):
        for i,v in enumerate(o[:400]): yield from find(v,key,path+'/'+str(i))
for p,v in find(r,'mismatches'): print(p, json.dumps(v)[:1500])
for p,v in find(r,'P1'): print(p, json.dumps({k:vv for k,vv in v.items() if k!='mismatches'})[:900] if isinstance(v,dict) else v)
EOF