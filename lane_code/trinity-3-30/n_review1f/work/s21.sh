W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=/scratch/jjyeung/orch_n30/n_review/r1e/tcpp; date -u +%TZ
mkdir -p /scratch/jjyeung/orch_n30/n_review/r1f
ls $W | tail -15; ls $W/work/d173725 2>&1; ls $W/w24t $W/w24t/out 2>&1 | head -40; ls -d $W/w24u 2>&1
echo "@@@ extent_receipt.py"; cat $T/student_pilot/extent_receipt.py | head -150
echo "@@@ grep"; grep -n "extent" $T/student_pilot/carrier_c1_run.py | head -30
