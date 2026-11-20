P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%TZ
nice -n 10 $P -I -s -B - <<'PY'
import json,base64,hashlib,os,tarfile
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'; T='/scratch/jjyeung/orch_n30/n_review/r1e/tcpp'
def dec(p):
    v=json.load(open(p)); r=base64.b64decode(v['payload']); return json.loads(r)
for kit in ('out/kit_n_go','out/kit_qd','work/build24/kits/q','work/build24/kits/n'):
    a=dec(W+'/w24j/'+kit+'/k/p.json'); b=dec(W+'/w24m/'+kit+'/k/p.json')
    ua={u['sha256']:u for u in a['uploads']}; ub={u['sha256']:u for u in b['uploads']}
    print(kit,'uploads',len(ua),'->',len(ub),'removed',[(h[:8],ua[h].get('bytes')) for h in ua if h not in ub],'added',[(h[:8],ub[h].get('bytes')) for h in ub if h not in ua])
    print('  other keys diff',[k for k in set(a)|set(b) if k not in ('uploads','pin_paths','code_sha256') and a.get(k)!=b.get(k)])
for kit in ('out/kit_n_go','out/kit_qd','work/build24/kits/q','work/build24/kits/n'):
    tp=W+'/w24m/'+kit+'/k/t_e047002134f979bd.tar'
    t=tarfile.open(tp); mism=0; n=0; names=set()
    for m in t.getmembers():
        if not m.isfile(): continue
        n+=1; name=m.name
        while name.startswith('./'): name=name[2:]
        names.add(name); h=hashlib.sha256(t.extractfile(m).read()).hexdigest(); q=os.path.join(T,name)
        if not os.path.exists(q) or hashlib.sha256(open(q,'rb').read()).hexdigest()!=h:
            mism+=1
            if mism<5: print('  TAR_MISMATCH',m.name)
    print(kit,'TREE_TAR',hashlib.sha256(open(tp,'rb').read()).hexdigest()[:16],'files',n,'mismatch_vs_my_Cpp',mism,sorted(names)[:2])
PY
