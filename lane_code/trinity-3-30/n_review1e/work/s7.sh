W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; P=/scratch/jjyeung/envs/p1cpu/bin/python; R=/scratch/jjyeung/orch_n30/n_review/r1e
date -u +%TZ
nice -n 10 $P -I -s -B - <<'PY'
import json,base64,hashlib,os,tarfile,io
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; T='/scratch/jjyeung/orch_n30/n_review/r1e/tcpp'
def dec(p):
    v=json.load(open(p))
    if isinstance(v,dict) and 'payload' in v:
        r=base64.b64decode(v['payload']); return json.loads(r), hashlib.sha256(r).hexdigest()
    return v, None
def walk(x,y,p=''):
    if isinstance(x,dict) and isinstance(y,dict):
        for k in sorted(set(x)|set(y)): walk(x.get(k,'<absent>'),y.get(k,'<absent>'),p+'/'+str(k))
    elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
        for i,(u,v) in enumerate(zip(x,y)): walk(u,v,p+'['+str(i)+']')
    elif x!=y: print('  DIFF',p,'|',json.dumps(x)[:300],'->',json.dumps(y)[:300])
for a,b in (('w24j/out/kit_n_go','w24m/out/kit_n_go'),('w24j/out/kit_qd','w24m/out/kit_qd'),('w24j/work/build24/kits/q','w24m/work/build24/kits/q'),('w24m/out/kit_n_go','w24m/out/kit_qd'),('w24m/out/kit_n_go','w24m/work/build24/kits/n')):
    print('########',a,'->',b)
    for f in sorted(os.listdir(W+'/'+b+'/k')):
        pa=W+'/'+a+'/k/'+f; pb=W+'/'+b+'/k/'+f
        if not f.endswith('.json'): continue
        if not os.path.exists(pa): print(b,f,'NEW'); continue
        if open(pa,'rb').read()==open(pb,'rb').read(): continue
        x,hx=dec(pa); y,hy=dec(pb); print('##',f,'payload',hx,'->',hy)
        walk(x,y)
# tree tar vs my C''
tp=W+'/w24m/out/kit_n_go/k/t_e047002134f979bd.tar'
t=tarfile.open(tp); mism=0; n=0; names=set()
for m in t.getmembers():
    if not m.isfile(): continue
    n+=1; name=m.name; 
    for pre in ('./','tree/','tree_r1/'):
        if name.startswith(pre): name=name[len(pre):]
    names.add(name)
    b=t.extractfile(m).read(); h=hashlib.sha256(b).hexdigest()
    q=os.path.join(T,name)
    if not os.path.exists(q) or hashlib.sha256(open(q,'rb').read()).hexdigest()!=h: mism+=1; print('TAR_MISMATCH',m.name) if mism<10 else None
print('TREE_TAR files',n,'mismatch_vs_my_Cpp',mism, 'sample names',sorted(names)[:3])
from subprocess import run
PY
