W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; du -s --block-size=1M $W/w24/work/tree_r1 /scratch/jjyeung/envs/p1cpu $W/w24 2>/dev/null; tmux ls | grep tr14
