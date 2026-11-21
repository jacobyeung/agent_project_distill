W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Y=$W/w24y2; Z=$W/w24z12; P=/scratch/jjyeung/envs/p1cpu/bin/python; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1h; T=$N/r1f/tcpx
mkdir -p $R
date -u +%TZ; hostname -s; df -h /scratch | tail -1
echo "== w24z12/out"; ls $Z/out < /dev/null | tr '\n' ' '; echo; ls $Z/work < /dev/null | tr '\n' ' '; echo; ls $Z/work/build24/kits < /dev/null 2>&1 | tr '\n' ' '; echo
ls -la $Z/out/*.tar* < /dev/null 2>/dev/null; cat $Z/out/*.tar.sha256 < /dev/null 2>/dev/null | cut -c1-120
sha256sum $Z/out/*.tar < /dev/null 2>/dev/null | cut -c1-100
sha256sum $Z/out/jn3.sh < /dev/null
echo "== kit seals"
for k in $Y/work/build24/kits/q $Z/work/build24/kits/q $Z/work/build24/kits/n $Z/out/kit_n_go $Z/out/kit_qd $Z/out/kit_n; do [ -d $k ] || { echo "ABSENT $k"; continue; }; echo "$k sums=$(sha256sum < $k/SHA256SUMS.txt|cut -c1-64) GO=$(grep -o '"GO": *[a-z]*' $k/BUILD.json 2>/dev/null)"; (cd $T && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$k'))" 2>&1 < /dev/null | tail -1); done
echo "== sums diffs 24m4y2 -> 24m4z12"; for p in work/build24/kits/q work/build24/kits/n out/kit_n_go out/kit_qd; do echo "-- $p"; [ -f $Z/$p/SHA256SUMS.txt ] || { echo absent; continue; }; diff <(sort -k2 $Y/$p/SHA256SUMS.txt) <(sort -k2 $Z/$p/SHA256SUMS.txt) | grep '^[<>]' | awk '{print $1, substr($2,1,12), $3}'; done
echo "== n vs n_go b/"; diff <(grep ' b/' $Z/work/build24/kits/n/SHA256SUMS.txt|sort -k2) <(grep ' b/' $Z/out/kit_n_go/SHA256SUMS.txt|sort -k2) | grep '^[<>]' | awk '{print $1,$3}' | tr '\n' ' '; echo
echo "== z4 -> z12 n_go b/ diffs"; diff <(sort -k2 $W/w24z4/out/kit_n_go/SHA256SUMS.txt) <(sort -k2 $Z/out/kit_n_go/SHA256SUMS.txt) | grep '^[<>]' | awk '{print $1, substr($2,1,12), $3}'
echo "== z10 -> z12 n_go diffs"; [ -d $W/w24z10/out/kit_n_go ] && diff <(sort -k2 $W/w24z10/out/kit_n_go/SHA256SUMS.txt) <(sort -k2 $Z/out/kit_n_go/SHA256SUMS.txt) | grep '^[<>]' | awk '{print $1, substr($2,1,12), $3}'
echo "== identity"
k=$Z/out/kit_n_go
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --ro-bind /scratch/jjyeung/uv-python /scratch/jjyeung/uv-python --tmpfs /tmp --ro-bind $T /tmp/x/tree --ro-bind $k/k /tmp/x/k --ro-bind $N/r1e/ident2.py /tmp/x/ident2.py --dev /dev --proc /proc --unshare-net --chdir /tmp/x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 $P -I -s -B /tmp/x/ident2.py > $R/ident_w24z12_tcpx.json 2>&1 < /dev/null
sha256sum $N/r1e/ident2.py $R/ident_w24z12_tcpx.json $k/k/c.json < /dev/null; grep -o "4794b27f[0-9a-f]*\|a1fd8b40[0-9a-f]*\|6d6fda1b[0-9a-f]*" $R/ident_w24z12_tcpx.json | sort | uniq -c
echo "== decoded"
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
for a,b in (('w24y2/out/kit_n_go','w24z12/out/kit_n_go'),('w24y2/work/build24/kits/n','w24z12/work/build24/kits/n'),('w24z12/out/kit_n_go','w24z12/work/build24/kits/n')):
    print('########',a,'->',b)
    if not os.path.isdir(W+'/'+b+'/k'): print('absent'); continue
    for f in sorted(os.listdir(W+'/'+b+'/k')):
        pa=W+'/'+a+'/k/'+f; pb=W+'/'+b+'/k/'+f
        if not f.endswith('.json') or f=='p.json': continue
        if not os.path.exists(pa): print(b,f,'NEW'); continue
        if open(pa,'rb').read()==open(pb,'rb').read(): continue
        x,hx=dec(pa); y,hy=dec(pb); print('##',f,'payload',hx,'->',hy); walk(x,y)
    if os.path.isdir(W+'/'+a+'/k'):
        print('only in a:',sorted(set(os.listdir(W+'/'+a+'/k'))-set(os.listdir(W+'/'+b+'/k'))))
for kit in ('out/kit_n_go','work/build24/kits/n'):
    a,_=dec(W+'/w24y2/'+kit+'/k/p.json'); b,_=dec(W+'/w24z12/'+kit+'/k/p.json')
    ua={u['sha256']:u for u in a['uploads']}; ub={u['sha256']:u for u in b['uploads']}
    print(kit,'p.json uploads',len(ua),'->',len(ub),'removed',[(h[:8],ua[h].get('bytes'),ua[h].get('name',ua[h].get('path','')) ) for h in ua if h not in ub],'added',[(h[:8],ub[h].get('bytes'),ub[h].get('name',ub[h].get('path',''))) for h in ub if h not in ua])
    print('  other keys diff',[k for k in set(a)|set(b) if k!='uploads' and a.get(k)!=b.get(k)])
for kit in ('out/kit_n_go','work/build24/kits/n','work/build24/kits/q'):
    d=W+'/w24z12/'+kit+'/k'
    if not os.path.isdir(d): print(kit,'absent'); continue
    tars=[f for f in os.listdir(d) if f.startswith('t_') and f.endswith('.tar')]
    for tf in tars:
        tp=d+'/'+tf; t=tarfile.open(tp); mism=0; n=0
        for m in t.getmembers():
            if not m.isfile(): continue
            n+=1; name=m.name
            while name.startswith('./'): name=name[2:]
            h=hashlib.sha256(t.extractfile(m).read()).hexdigest(); q=os.path.join(T,name)
            if not os.path.exists(q) or hashlib.sha256(open(q,'rb').read()).hexdigest()!=h:
                mism+=1
                if mism<5: print('  TAR_MISMATCH',m.name)
        print(kit,tf,'TREE_TAR',hashlib.sha256(open(tp,'rb').read()).hexdigest()[:16],'files',n,'mismatch_vs_tcpx',mism)
PY
echo "== b diffs n_go 24m4z10 -> 24m4z12 (pc.py)"; diff -u $W/w24z10/out/kit_n_go/b/pc.py $Z/out/kit_n_go/b/pc.py < /dev/null | head -150
echo "== arm runner"; ls $W/w24z11b/out < /dev/null | tr '\n' ' '; echo; sha256sum $W/w24z11b/out/arm_launch.sh $W/w24z11b/out/arm_routing.py $Z/out/kit_n_go/b/arm_routing.py $W/w24y2/out/arm_routing.py < /dev/null 2>&1
