T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go; date -u +%TZ
grep -n -E "R1_HOST_ADMISSION_MISSING|INDEPENDENT_REVIEW_PENDING|host_receipt|'review'|def admit" $T/launch_r1/*.py </dev/null | head -20 | cut -c1-220
grep -n -E "host_receipt|review" $K/b/a.py $K/b/h.py $K/b/u.py $K/b/z.py $K/b/g.py </dev/null | head -20 | cut -c1-220
