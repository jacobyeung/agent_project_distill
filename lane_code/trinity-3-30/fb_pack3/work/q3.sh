F=/scratch/jjyeung/orch_n30/fb_pack/cam/out; ls -la $F/intake $F/rows | head -20; head -c 1500 $F/INTAKE.json; echo; for f in $F/intake/camera_wording_shard000.json; do head -c 1200 $f; echo; done
/scratch/jjyeung/envs/p1cpu/bin/python - <<'P'
import json
d=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/cam/out/intake/camera_wording_shard000.json'))
def sk(o,dep=0):
    if isinstance(o,dict):
        for k,v in list(o.items())[:30]:
            print('  '*dep+k, type(v).__name__, (len(v) if hasattr(v,'__len__') else v) if not isinstance(v,(int,float,bool)) else v)
            if dep<2: sk(v,dep+1)
    elif isinstance(o,list) and o: sk(o[0],dep+1)
sk(d)
P
