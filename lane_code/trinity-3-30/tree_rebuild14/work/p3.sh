W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; P=$W/work/conf24c/pkg; ls $P/work $P/out | head -30; ls $W/w24/work | tr '\n' ' '; echo
for d in $P/work/*/ $W/w24/work/*/; do test -f $d/student_pilot/carrier_c1_run.py && echo TREE=$d; done
sed -n 250,330p /tmp/tr14_j.sh </dev/null | cut -c1-220
sed -n 380,412p /tmp/tr14_j.sh </dev/null | cut -c1-260
