W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24/work/tree_r1; K=$W/w24/out/kit_n_go; date -u +%TZ
grep -n -E "frame_host|host_receipt|review" $T/launch_r1/production_proof.py $T/launch_r1/build.py $K/b/a.py $K/b/z.py </dev/null | head -20 | cut -c1-200
grep -n -E "host|review" $W/w24/work/build24d/fixture_gates.py </dev/null | head -12 | cut -c1-200
tmux ls | grep tr14
