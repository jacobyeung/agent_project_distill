W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; X=$W/w24x2; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1f; PY=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ; cd $R
cp $X/out/TREE_CHANGE_24M4X.patch $R/p24m4x.patch; sha256sum p24m4x.patch; wc -l p24m4x.patch
[ -d tcpx ] || cp -a $N/r1e/tcpp tcpx
cd tcpx && patch -p1 --dry-run < $R/p24m4x.patch > /dev/null && patch -p1 < $R/p24m4x.patch
nice -n 10 $PY -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print('tcpx',len(f), digest(f))"
sha256sum student_pilot/extent_receipt.py student_pilot/carrier_c1_run.py student_pilot/r1_routing.py student_pilot/r2_intake.py
echo "@@@ diff C'' vs x"; diff -r $N/r1e/tcpp $R/tcpx | head -80
echo "@@@ diff T vs x"; diff -r $R/tcpt $R/tcpx | head -40
