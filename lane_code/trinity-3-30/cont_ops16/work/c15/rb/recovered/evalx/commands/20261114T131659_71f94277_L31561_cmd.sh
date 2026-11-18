<!-- recovered by seal_plan: transcript=71f94277 line=31561 utc=2026-11-14T13:16:59.719Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json,hashlib,os
B='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
new=B+'native_probe_s23_01/seal/FAMILY.json'
old=None
for cand in ('native_fix_s23_01/orchard_native/seal_s23_01/FAMILY.json',):
    if os.path.exists(B+cand): old=B+cand
print('old',old)
n=json.load(open(new)); print('new sha',hashlib.sha256(open(new,'rb').read()).hexdigest()[:16], list(n.keys())[:30])
if old:
    o=json.load(open(old)); print('old sha',hashlib.sha256(open(old,'rb').read()).hexdigest()[:16])
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
    for k in ch[:60]: print(k[:110],'|',str(fo.get(k))[:40],'->',str(fn.get(k))[:40])
EOF