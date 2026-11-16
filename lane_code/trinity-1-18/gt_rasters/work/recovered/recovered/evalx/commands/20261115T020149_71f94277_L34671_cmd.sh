<!-- recovered by seal_plan: transcript=71f94277 line=34671 utc=2026-11-15T02:01:49.357Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_04; sha256sum $D/RUNTIME.diff | cut -c1-16; wc -l $D/RUNTIME.diff; cut -c1-220 $D/RUNTIME.diff | head -n 40; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json,hashlib
B='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
new=B+'native_package_s24_04/seal/FAMILY.json'; old=B+'native_package_s24_03/seal/FAMILY.json'
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
for k in ch[:30]: print(' ',k[-80:],'|',str(fo.get(k))[:18],'->',str(fn.get(k))[:18])
c=json.load(open(B+'native_package_s24_04/pilot_candidate_advanced/CONFIG.json'))
print({k:c.get(k) for k in ('mode','partition','step','token')}, c['worker']['artifact']['sha256'][:16])
EOF