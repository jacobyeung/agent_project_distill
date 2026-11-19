W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24/work/tree_r1
date -u +%TZ; df -h /scratch | tail -1
echo "== out"; ls -lt $W/w24/out | head -30
echo "== kit_n_go b"; ls -l $W/w24/out/kit_n_go/b | head -60
echo "== tree top"; ls $T; ls $T/launch_r1 $T/launch_r2 2>/dev/null | head -80
echo "== scene files"; ls $T/student_pilot | grep -i "r2_\|scene\|s1_rout" 
echo "== x24l3_back"; ls -la $W/work/x24l3_back 2>&1 | head
echo "== n_review"; ls -la /scratch/jjyeung/orch_n30/n_review | head -40
