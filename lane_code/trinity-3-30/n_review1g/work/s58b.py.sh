P=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ
nice -n 10 $P -I -s -B - <<'PY'
import json,base64,hashlib,os,tarfile
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; T='/scratch/jjyeung/orch_n30/n_review/r1f/tcpx'
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
    elif x!=y: print('  DIFF',p,'|',json.dumps(x)[:240],'->',json.dumps(y)[:240])
for a,b in (('w24y2/out/kit_n_go','w24z4/out/kit_n_go'),('w24y2/work/build24/kits/n','w24z4/work/build24/kits/n'),('w24z4/out/kit_n_go','w24z4/work/build24/kits/n')):
    print('########',a,'->',b)
    for f in sorted(os.listdir(W+'/'+b+'/k')):
        pa=W+'/'+a+'/k/'+f; pb=W+'/'+b+'/k/'+f
        if not f.endswith('.json') or f=='p.json': continue
        if not os.path.exists(pa): print(b,f,'NEW'); continue
        if open(pa,'rb').read()==open(pb,'rb').read(): continue
        x,hx=dec(pa); y,hy=dec(pb); print('##',f,'payload',hx,'->',hy); walk(x,y)
for kit in ('out/kit_n_go',):
    a,_=dec(W+'/w24y2/'+kit+'/k/p.json'); b,_=dec(W+'/w24z4/'+kit+'/k/p.json')
    ua={u['sha256']:u for u in a['uploads']}; ub={u['sha256']:u for u in b['uploads']}
    print(kit,'p.json uploads',len(ua),'->',len(ub),'removed',[(h[:8],ua[h].get('bytes'),ua[h].get('name',ua[h].get('path','')) ) for h in ua if h not in ub],'added',[(h[:8],ub[h].get('bytes'),ub[h].get('name',ub[h].get('path',''))) for h in ub if h not in ua])
    print('  other keys diff',[k for k in set(a)|set(b) if k!='uploads' and a.get(k)!=b.get(k)])
for kit in ('out/kit_n_go','out/kit_qd','work/build24/kits/q','work/build24/kits/n'):
    tp=W+'/w24z4/'+kit+'/k/t_e047002134f979bd.tar'; t=tarfile.open(tp); mism=0; n=0
    for m in t.getmembers():
        if not m.isfile(): continue
        n+=1; name=m.name
        while name.startswith('./'): name=name[2:]
        h=hashlib.sha256(t.extractfile(m).read()).hexdigest(); q=os.path.join(T,name)
        if not os.path.exists(q) or hashlib.sha256(open(q,'rb').read()).hexdigest()!=h:
            mism+=1
            if mism<5: print('  TAR_MISMATCH',m.name)
    print(kit,'TREE_TAR',hashlib.sha256(open(tp,'rb').read()).hexdigest()[:16],'files',n,'mismatch_vs_tcpx',mism)
PY
