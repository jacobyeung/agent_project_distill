W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/out/kit_n_go; date -u +%TZ; tmux ls 2>&1 | grep -E "tr1[34]"
sed -n 1,30p $K/b/pc.py </dev/null | cut -c1-200; echo ...; sed -n 170,215p $K/b/pc.py </dev/null | cut -c1-200
grep -n "pc.py" $K/job.sh </dev/null | cut -c1-250
