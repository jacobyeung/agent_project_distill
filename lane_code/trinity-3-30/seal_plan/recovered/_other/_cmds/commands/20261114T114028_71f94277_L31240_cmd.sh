<!-- recovered by seal_plan: transcript=71f94277 line=31240 utc=2026-11-14T11:40:28.209Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import os,hashlib
A='/scratch/jjyeung/orch_cd/if_p0/out/modes_v7/kit_ifp0_orchard_job_799a21dd2eef37af'
B='/scratch/jjyeung/orch_cd/if_p0/out/guards_v8/kit_ifp0_orchard_job_eef3ba96a639d634'
def walk(r):
    out={}
    for d,_,fs in os.walk(r):
        for f in fs:
            p=os.path.join(d,f); out[os.path.relpath(p,r)]=hashlib.sha256(open(p,'rb').read()).hexdigest()
    return out
a,b=walk(A),walk(B)
print(len(a),len(b))
print('only old:',sorted(set(a)-set(b)))
print('only new:',sorted(set(b)-set(a)))
print('changed:',sorted(k for k in a if k in b and a[k]!=b[k]))
EOF