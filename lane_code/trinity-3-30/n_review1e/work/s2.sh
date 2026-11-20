W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1e; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%TZ; mkdir -p $R; cd $R || exit 1
seal(){ (cd $1 && nice -n 10 env OMP_NUM_THREADS=2 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); }
[ -d tcpp ] || cp -a $N/r1b/tc/work/tree_r1 tcpp
echo "C copy seal: $(seal tcpp)"
(cd tcpp && patch -p1 --no-backup-if-mismatch < $W/w24k/out/TREE_CHANGE_24M4K.patch && patch -p1 --no-backup-if-mismatch < /scratch/jjyeung/orch_n30/tr19_revC1/work/TEST_HOST24J_FIX.patch)
echo "C'' seal: $(seal tcpp)"
sha256sum tcpp/student_pilot/carrier_c1_run.py tcpp/launch_r1/entry.py tcpp/tests/test_host24j.py tcpp/tests/test_r1_processor_compat.py
cat $N/r1b/ident2.py
ls -la $W/w24l $W/w24l/out $W/w24m $W/w24m/out 2>&1 | head -70
cat $W/w24l/out/*REPORT*.md 2>/dev/null | head -c 6000
