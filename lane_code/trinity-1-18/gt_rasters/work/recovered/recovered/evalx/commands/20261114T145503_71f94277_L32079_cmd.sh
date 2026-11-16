<!-- recovered by seal_plan: transcript=71f94277 line=32079 utc=2026-11-14T14:55:03.373Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json,hashlib
B='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
new=B+'native_p1_s23_01/seal/FAMILY.json'; old=B+'native_probe_s23_01/seal/FAMILY.json'
n=json.load(open(new)); o=json.load(open(old))
print('new',hashlib.sha256(open(new,'rb').read()).hexdigest()[:16],'old',hashlib.sha256(open(old,'rb').read()).hexdigest()[:16])
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
for k in ch[:60]: print(k[-95:],'|',str(fo.get(k))[:24],'->',str(fn.get(k))[:24])
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1454Z: P1/report candidate sealed = family e58e5a1e; advanced pilot-4 token e2daae3c9; general fallback e953c2664; code object code_aec086b11a317afe.tar gen 1794667992194350. Review still running; control files after its verdict." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md