W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; M=/scratch/jjyeung/orch_n30/n_review; T=$W/w24/work/tree_r1
cat > $M/ident.py <<'PYEOF'
import sys,json,base64,hashlib
sys.path.insert(0,'/tmp/x/tree')
from student_pilot.carrier_c1_run import identity
from student_pilot.p3_provenance import digest
out={}
for name in ('c','n'):
    raw=open(f'/tmp/x/k/{name}.json','rb').read(); v=json.loads(raw); b=base64.b64decode(v['payload'])
    assert hashlib.sha256(b).hexdigest()==v['sha256']
    cfg=json.loads(b)
    out[name]=dict(file_sha256=hashlib.sha256(raw).hexdigest(),payload_sha256=v['sha256'],identity=identity(cfg))
try:
    from student_pilot.r1_handover import stream_identity
    from student_pilot.p3_provenance import load
    cfg=json.loads(base64.b64decode(json.load(open('/tmp/x/k/c.json'))['payload']))
    st={}
    import os; os.chdir('/x')
    for s,pin in cfg['streams'].items():
        st[s]=stream_identity(json.load(open('/tmp/x/'+pin['path'])),s)
    out['stream_identity_from_receipts']=st
except Exception as e: out['stream_identity_error']=repr(e)[:500]
print(json.dumps(out,indent=1))
PYEOF
du -sh $T; mkdir -p $M/tree && cp -a $T/. $M/tree/ && (cd $M/tree && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print('copy seal',len(f), digest(f))")
echo "== identity hidden view"
nice -n 10 bwrap --ro-bind / / --tmpfs /home --tmpfs /data --tmpfs /data2 --tmpfs /data3 --tmpfs /scratch/jjyeung   --ro-bind /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/envs/p1cpu --tmpfs /tmp --ro-bind $M/tree /tmp/x/tree --ro-bind $M/x/k /tmp/x/k --ro-bind $M/x/u /tmp/x/u --ro-bind $M/ident.py /tmp/x/ident.py   --dev /dev --proc /proc --unshare-net --chdir /tmp/x env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=2 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /tmp/x/ident.py > $M/ident_out.json 2>&1; cat $M/ident_out.json; sha256sum $M/ident_out.json
echo "== test build19"; sed -n 95,150p $M/tree/tests/test_r1_build19.py
cd $M/tree && OMP_NUM_THREADS=2 nice -n 10 timeout 600 /scratch/jjyeung/envs/p1cpu/bin/python -B -m unittest tests.test_r1_build19 2>&1 | tail -8
echo "== r2_policy 100-124"; sed -n 100,124p $M/tree/student_pilot/r2_policy.py
echo "== r1_persisted 190-212"; sed -n 190,212p $M/tree/student_pilot/r1_persisted.py
echo "== r2_contract 25-45"; sed -n 25,45p $M/tree/student_pilot/r2_contract.py
grep -n "^SCOPE\|^LINEAGE\|^EXTERNAL\|^NEW\|^CHOICES" $M/tree/student_pilot/r2_policy.py
