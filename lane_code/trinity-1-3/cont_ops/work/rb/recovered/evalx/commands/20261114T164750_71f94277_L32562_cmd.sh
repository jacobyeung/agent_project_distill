<!-- recovered by seal_plan: transcript=71f94277 line=32562 utc=2026-11-14T16:47:50.091Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json,hashlib,os,tarfile
B='/scratch/jjyeung/orch_cd/evalx/work/milestone/'
new=B+'native_package_s23_02/seal/FAMILY.json'; old=B+'native_p1_s23_02/seal/FAMILY.json'
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
for k in ch[:60]: print(k[-78:],'|',str(fo.get(k))[:18],'->',str(fn.get(k))[:18])
# members vs pins
obj=n['assets']['small_objects'][0]; mem=obj['members']; pins=n['code_pins']
def norm(p): return p.split('/sj/',1)[-1] if '/sj/' in p else p.lstrip('/').replace('sj/','',1) if p.startswith('sj/') else p
pm={k.replace('/scratch/jjyeung/','',1):v for k,v in pins.items()}
bad=[];nopin=[]
for path,meta in mem.items():
    key=path.replace('sj/','',1) if path.startswith('sj/') else path
    sha=meta.get('sha256') if isinstance(meta,dict) else meta
    if key in pm:
        if pm[key]!=sha: bad.append((key,sha[:12],pm[key][:12]))
    else: nopin.append(key)
print('members',len(mem),'code pins',len(pins),'mismatch',bad,'members without a code pin',len(nopin), nopin[:12])
missing=[k for k in pm if ('sj/'+k) not in mem and k not in mem]
print('pins without a member',len(missing), missing[:12])
# verify the local archive bytes too
import glob
cands=glob.glob(B+'native_package_s23_02/**/code_698766e61697edf0.tar',recursive=True)
print('local archive',cands[:2])
if cands:
    a=cands[0]; print(hashlib.sha256(open(a,'rb').read()).hexdigest()[:16], os.path.getsize(a))
    t=tarfile.open(a); mm=0; tot=0
    for m in t.getmembers():
        if not m.isfile(): continue
        tot+=1; h=hashlib.sha256(t.extractfile(m).read()).hexdigest()
        key=m.name.replace('sj/','',1) if m.name.startswith('sj/') else m.name
        if key in pm and pm[key]!=h: mm+=1; print('ARCHIVE MISMATCH',key)
        if m.name in mem and (mem[m.name].get('sha256') if isinstance(mem[m.name],dict) else mem[m.name])!=h: print('MEMBER LIST MISMATCH',m.name)
    print('archive files',tot,'pin mismatches',mm)
EOF