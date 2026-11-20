W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; H=$W/w24h; P=/scratch/jjyeung/envs/p1cpu/bin/python; M=/scratch/jjyeung/orch_n30/n_review/r1b; R=/scratch/jjyeung/orch_n30/n_review/r1c
date -u +%TZ
sha256sum $H/out/tree_rebuild_b24m4h_0eed8bc7.tar
echo "== kit seals"; for k in $H/work/build24/kits/q $H/work/build24/kits/n $H/out/kit_n_go $H/out/kit_qd; do echo "$k sums=$(sha256sum < $k/SHA256SUMS.txt|cut -c1-64)"; (cd $W/w24c/work/tree_r1 && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$k'))" 2>&1 | tail -1); done
echo "== n_go sums diff vs 24m4e"; diff <(sort -k2 $W/w24e/out/kit_n_go/SHA256SUMS.txt) <(sort -k2 $H/out/kit_n_go/SHA256SUMS.txt)
echo "== qd vs n_go"; diff <(sort -k2 $H/out/kit_qd/SHA256SUMS.txt) <(sort -k2 $H/out/kit_n_go/SHA256SUMS.txt) | grep ' b/' 
echo "== identity"
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --ro-bind /scratch/jjyeung/uv-python /scratch/jjyeung/uv-python --tmpfs /tmp --ro-bind $M/tc/work/tree_r1 /tmp/x/tree --ro-bind $H/out/kit_n_go/k /tmp/x/k --ro-bind $M/ident2.py /tmp/x/ident2.py --dev /dev --proc /proc --unshare-net --chdir /tmp/x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 $P -I -s -B /tmp/x/ident2.py > $R/ident_24m4h.json 2>&1; sha256sum $R/ident_24m4h.json; cat $R/ident_24m4h.json
echo "== c.json diff"
$P -I -s -B - <<'PY'
import json,base64
def dec(p): v=json.load(open(p)); return json.loads(base64.b64decode(v['payload']))
W='/scratch/jjyeung/orch_n30/tree_rebuild10_w'
a=dec(W+'/w24e/out/kit_n_go/k/c.json'); b=dec(W+'/w24h/out/kit_n_go/k/c.json')
def walk(x,y,p=''):
    if isinstance(x,dict) and isinstance(y,dict):
        for k in sorted(set(x)|set(y)): walk(x.get(k,'<absent>'),y.get(k,'<absent>'),p+'/'+str(k))
    elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
        for i,(u,v) in enumerate(zip(x,y)): walk(u,v,p+'['+str(i)+']')
    elif x!=y: print('DIFF',p,'|',json.dumps(x)[:300],'->',json.dumps(y)[:300])
walk(a,b)
PY
