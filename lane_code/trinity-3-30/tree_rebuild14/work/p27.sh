W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/out/kit_n_go; date -u +%TZ; tmux ls 2>&1 | grep -E "tr1[34]"
sed -n 40,60p $K/b/pc.py </dev/null | cut -c1-220; cat $K/b/pc.sh </dev/null | head -30; grep -n "pc.sh" $K/job.sh </dev/null
ls $W/w24/out | grep -E "b24f|DELIVERY_24F"
