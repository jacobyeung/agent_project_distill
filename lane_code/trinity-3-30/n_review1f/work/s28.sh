W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; N=/scratch/jjyeung/orch_n30/n_review; R=$N/r1f; PY=/scratch/jjyeung/envs/p1cpu/bin/python; O=$W/w24v/out
date -u +%TZ; mkdir -p $R; cd $R || exit 1
[ -d tcpt ] || cp -a $N/r1e/tcpp tcpt
cp $O/TREE_CHANGE_24M4V.patch $R/p24m4v.patch; sha256sum p24m4v.patch
cd tcpt && patch -p1 --dry-run < $R/p24m4v.patch && patch -p1 < $R/p24m4v.patch; ls *.orig */*.orig 2>/dev/null
nice -n 10 $PY -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print('tcpt',len(f), digest(f))"
sha256sum student_pilot/extent_receipt.py student_pilot/carrier_c1_run.py student_pilot/r1_routing.py student_pilot/r2_intake.py
echo "@@@ readers"; grep -rn "Extents(\|extent_pool_sources\|\.exempted\|box_statuses\|repair_sha256" --include=*.py student_pilot launch_r1 2>/dev/null | head -40
echo "@@@ r1_training keys"; grep -rn "r1_training\[.\|r1_training.get\|'r1_training'" --include=*.py student_pilot launch_r1 | head -30
ls tests | grep -i -E "extent|intake|r1_routing|carrier|host24|r1_train|launch22" | head
echo "@@@ report"; ls $O/*24M4V*; grep -n -i "seal\|7a8022ad\|test" $O/BUILD24M4V_REPORT.md | head -40
