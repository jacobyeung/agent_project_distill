T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go; date -u +%TZ
sed -n 60,110p $T/launch_r1/entry.py </dev/null | cut -c1-220
grep -n -l -E "host_receipt" $K/b/*.py $T/launch_r1/*.py </dev/null
