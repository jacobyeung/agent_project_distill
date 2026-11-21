F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w27fix
date -u +%TZ; tmux has-session -t w27run3 2>/dev/null && echo RUNNING || echo FINISHED
cut -c1-2300 $F/work/run3.out
