W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; S=$W/work/up24c; test ! -e $S && mkdir -p $S
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,os,hashlib
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; S=W+'/work/up24c'
def entries(j):
    d=json.load(open(j)); out={}
    def walk(x):
        if isinstance(x,dict):
            if 'local_path' in x and ('name' in x or 'opaque_name' in x): out[x.get('name') or x.get('opaque_name')]=x
            else:
                for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(d); return out
final={}
for tag in ('24B','24C'):
    e=entries(W+'/w24/out/UPLOADS_%s.json'%tag)
    names=[l.strip() for l in open(W+'/w24/out/UPLOADS_%s.list'%tag) if l.strip()]
    print(tag,'list',len(names),'json',len(e),'missing',[n for n in names if n not in e][:3])
    for n in names: final[n]=e[n]
tot=0; sums=[]
for n,x in sorted(final.items()):
    p=x['local_path']; h=hashlib.sha256(open(p,'rb').read()).hexdigest(); assert h==x['sha256'],n
    dst=os.path.join(S,n); os.makedirs(os.path.dirname(dst),exist_ok=True)
    if not os.path.lexists(dst): os.symlink(p,dst)
    tot+=os.path.getsize(p); sums.append('%s  %s'%(h,n))
open(W+'/work/up24c.sha','w').write('\n'.join(sums)+'\n')
print('final',len(final),'bytes',tot,'tops',sorted({n.split('/')[0] for n in final}))
PY
cd $S && tar chf - $(ls) | wc -c; cat $W/work/up24c.sha | wc -l
