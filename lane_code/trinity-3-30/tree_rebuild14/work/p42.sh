W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; tmux ls | grep tr14
if ! tmux has-session -t tr14_b24fr 2>/dev/null && ! tmux has-session -t tr14_reh2 2>/dev/null; then
 tmux new -d -s tr14_reh2 "cd $W/w24 && nice -n 10 bash work/build24f/go_rehearsal.sh > $W/w24/work/build24f/rehearsal_run2.log 2>&1; echo RC=\$? >> $W/w24/work/build24f/rehearsal_run2.log"; echo STARTED_REH2; fi
sleep 5; tmux ls | grep tr14
