F=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28fix
date -u +%TZ; tmux has-session -t w28a 2>/dev/null && echo RUNNING || echo DONE
cat $F/work/cpu1.out | cut -c1-1700
