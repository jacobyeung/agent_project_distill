cd /scratch/jjyeung/orch_n30
sha256sum b05_owngrd/work/manifests/TEACHER_K1.json b10_reserve/out/R0_SCENES.json b10_reserve/out/R0_ROOMS.txt
ls -la b05_owngrd/work/manifests/TEACHER_K1.json b10_reserve/out/R0_SCENES.json
python3 - <<'PY'
import json
m=json.load(open('b05_owngrd/work/manifests/TEACHER_K1.json'))
def keys(x,d=0):
    if isinstance(x,dict): return {k:(keys(v,d+1) if d<1 else type(v).__name__) for k,v in list(x.items())[:12]}
    if isinstance(x,list): return ['list',len(x), keys(x[0],d+1) if x else None]
    return type(x).__name__
print('SCHEMA', json.dumps(keys(m))[:1500])
PY
