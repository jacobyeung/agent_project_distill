import itertools, json, subprocess, sys
U='41125829 41126341 42898477 42898715 42899325 43895863 45261007 45261532 47115265 47332204'.split()
base={"dt":"us","floor":"A","band":True}
res=[]
for p64,inv,xf,ray,pre,f32 in itertools.product([True,False],['linalg','T'],['hom','rt','ein','f32h'],['div','mulfirst','kinv'],[False,True],[False,True]):
    if inv=='T' and not p64 and xf!='f32h': pass
    o=dict(base,pose64=p64,inv=inv,xf=xf,ray=ray,prerot=pre,f32=f32)
    name='sw_'+'_'.join(str(int(v)) if isinstance(v,bool) else v for v in (p64,inv,xf,ray,pre,f32))
    out=subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','runv.py',name,json.dumps(o)]+U,capture_output=True,text=True).stdout
    rows=[json.loads(l) for l in open(f'/scratch/jjyeung/orch_n30/gt_build2/logs/VARIANT_{name}.jsonl')][1:]
    m=sorted(r['c'] for r in rows if r.get('match'))
    print(name,len(m),m,flush=True)
