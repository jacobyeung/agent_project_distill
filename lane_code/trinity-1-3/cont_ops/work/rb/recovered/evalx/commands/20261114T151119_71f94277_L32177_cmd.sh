<!-- recovered by seal_plan: transcript=71f94277 line=32177 utc=2026-11-14T15:11:19.925Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json,hashlib
B='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
new=B+'native_p1_s23_02/seal/FAMILY.json'; old=B+'native_p1_s23_01/seal/FAMILY.json'
n=json.load(open(new)); o=json.load(open(old))
print('new',hashlib.sha256(open(new,'rb').read()).hexdigest(),'old',hashlib.sha256(open(old,'rb').read()).hexdigest()[:16])
def flat(d,p=''):
    out={}
    if isinstance(d,dict):
        for k,v in d.items(): out.update(flat(v,p+'/'+str(k)))
    elif isinstance(d,list):
        for i,v in enumerate(d): out.update(flat(v,p+'/'+str(i)))
    else: out[p]=d
    return out
fo,fn=flat(o),flat(n)
ch=[k for k in sorted(set(fo)|set(fn)) if fo.get(k)!=fn.get(k)]
print(len(fo),len(fn),'changed',len(ch))
for k in ch[:40]: print(k[-80:],'|',str(fo.get(k))[:20],'->',str(fn.get(k))[:20])
print(n.get('partitions'))
EOF
sha256sum /scratch/jjyeung/orch_cd/evalx/work/milestone/native/out2/nomdg.py /scratch/jjyeung/orch_cd/evalx/work/milestone/native_fix_s23_01/orchard_native/native_worker.py | cut -c1-24,65-; ls /scratch/jjyeung/orch_cd/evalx/work/milestone/native_p1_s23_02/pilot_candidate_advanced | head