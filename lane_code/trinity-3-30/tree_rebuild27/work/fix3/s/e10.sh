F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w27fix
date -u +%TZ; tmux has-session -t w27run4 2>/dev/null && echo RUNNING || echo FINISHED
cat $F/work/run4.out | cut -c1-6000
