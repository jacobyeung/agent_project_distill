W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; H=$W/w24h; I=$W/w24i; P=/scratch/jjyeung/envs/p1cpu/bin/python; M=/scratch/jjyeung/orch_n30/n_review/r1b; R=/scratch/jjyeung/orch_n30/n_review/r1d
date -u +%TZ
sha256sum $I/out/tree_rebuild_b24m4i_ca5561be.tar; ls $I/work/build24m4i | head -40; ls $I/work/build24/kits
echo "== kit seals"; for k in $I/work/build24/kits/q $I/work/build24/kits/n $I/out/kit_n_go $I/out/kit_qd; do echo "$k sums=$(sha256sum < $k/SHA256SUMS.txt|cut -c1-64)"; (cd $W/w24c/work/tree_r1 && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$k'))" 2>&1 | tail -1); done
echo "== sums diffs 24m4h -> 24m4i"; diff <(sort -k2 $H/work/build24/kits/q/SHA256SUMS.txt) <(sort -k2 $I/work/build24/kits/q/SHA256SUMS.txt); echo "-- n"; diff <(sort -k2 $H/work/build24/kits/n/SHA256SUMS.txt) <(sort -k2 $I/work/build24/kits/n/SHA256SUMS.txt); echo "-- n_go"; diff <(sort -k2 $H/out/kit_n_go/SHA256SUMS.txt) <(sort -k2 $I/out/kit_n_go/SHA256SUMS.txt); echo "-- qd"; diff <(sort -k2 $H/out/kit_qd/SHA256SUMS.txt) <(sort -k2 $I/out/kit_qd/SHA256SUMS.txt)
echo "== identity"
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --ro-bind /scratch/jjyeung/uv-python /scratch/jjyeung/uv-python --tmpfs /tmp --ro-bind $M/tc/work/tree_r1 /tmp/x/tree --ro-bind $I/out/kit_n_go/k /tmp/x/k --ro-bind $M/ident2.py /tmp/x/ident2.py --dev /dev --proc /proc --unshare-net --chdir /tmp/x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 $P -I -s -B /tmp/x/ident2.py > $R/ident_24m4i.json 2>&1; sha256sum $R/ident_24m4i.json; cat $R/ident_24m4i.json
echo "== c.json/n.json/q-kit json decoded diffs (all k/*.json that differ, all four kits)"
$P -I -s -B - <<'PY'
import json,base64,hashlib
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'
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
    elif x!=y: print('  DIFF',p,'|',json.dumps(x)[:400],'->',json.dumps(y)[:400])
import os
for a,b in (('w24h/work/build24/kits/q','w24i/work/build24/kits/q'),('w24h/work/build24/kits/n','w24i/work/build24/kits/n'),('w24h/out/kit_n_go','w24i/out/kit_n_go'),('w24h/out/kit_qd','w24i/out/kit_qd')):
    for f in sorted(os.listdir(W+'/'+b+'/k')):
        pa=W+'/'+a+'/k/'+f; pb=W+'/'+b+'/k/'+f
        if not f.endswith('.json'): continue
        if not os.path.exists(pa): print(b,f,'NEW'); continue
        if open(pa,'rb').read()==open(pb,'rb').read(): continue
        x,hx=dec(pa); y,hy=dec(pb); print('##',b,f,'payload',hx,'->',hy)
        walk(x,y)
PY
