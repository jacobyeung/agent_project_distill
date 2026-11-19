W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; M=/scratch/jjyeung/orch_n30/n_review; T=$W/w24/work/tree_r1
mkdir -p $M/x/k $M/x/u; cp $W/w24/out/kit_n_go/k/c.json $W/w24/out/kit_n_go/k/n.json $M/x/k/
for h in ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984 93b21a3aeeda01efab90d9f818eff78a6ca182c18c964534279008e4af91733a e3ee51daa46af30fa8e84a05c12448d7fc3dc9cade05284707f9df322bbe44d0; do cp -L $W/w24/work/build22/upload/u/$h $M/x/u/; done
cp -L $(ls $W/w24/work/*/upload*/u/8957d119bfa6776efe776816675da6d0f610a6e8c336acd66c297f29cf4e7e0f $W/work/up24/u/8957d119bfa6776efe776816675da6d0f610a6e8c336acd66c297f29cf4e7e0f 2>/dev/null | head -1) $M/x/u/ 2>&1
ls -la $M/x/u; sha256sum $M/x/u/* | cut -c1-20
cat > $M/ident.py <<'PYEOF'
import sys,json,base64,hashlib
sys.path.insert(0,'/x/tree')
from student_pilot.carrier_c1_run import identity
from student_pilot.p3_provenance import digest
out={}
for name in ('c','n'):
    raw=open(f'/x/k/{name}.json','rb').read(); v=json.loads(raw); b=base64.b64decode(v['payload'])
    assert hashlib.sha256(b).hexdigest()==v['sha256']
    cfg=json.loads(b)
    out[name]=dict(file_sha256=hashlib.sha256(raw).hexdigest(),payload_sha256=v['sha256'],identity=identity(cfg))
try:
    from student_pilot.r1_handover import stream_identity
    from student_pilot.p3_provenance import load
    cfg=json.loads(base64.b64decode(json.load(open('/x/k/c.json'))['payload']))
    st={}
    import os; os.chdir('/x')
    for s,pin in cfg['streams'].items():
        st[s]=stream_identity(json.load(open('/x/'+pin['path'])),s)
    out['stream_identity_from_receipts']=st
except Exception as e: out['stream_identity_error']=repr(e)[:500]
print(json.dumps(out,indent=1))
PYEOF
echo "== tree seal"; (cd $T && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))")
echo "== identity hidden view"
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung   --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --ro-bind $T /x/tree --ro-bind $M/x/k /x/k --ro-bind $M/x/u /x/u --ro-bind $M/ident.py /x/ident.py   --dev /dev --proc /proc --tmpfs /tmp --unshare-net --chdir /x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /x/ident.py 2>&1 | tee $M/ident_out.json
echo "== stream_identity src"; grep -n "def stream_identity" -A25 $T/student_pilot/r1_handover.py
