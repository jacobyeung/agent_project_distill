set -u
J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28jn7
tmux kill-session -t fix5_t7; pkill -TERM -f "$J/t7/t_jn7"; sleep 5; pgrep -af "$J/t7" | cut -c1-150
tail -5 $J/t7.log
mv $J/t7 $J/t7_v2b; mv $J/t7.log $J/t7_v2b.log; mkdir -p $J/t7c; cp $J/out/jn7.sh $J/src/j6.py $J/t7c/
tmux new -d -s fix5_t7 "cd $J && nice -n 10 bash $J/src3/t7.sh $J/t7c > $J/t7c.log 2>&1; date -u > $J/t7c.DONE"
sleep 1; tmux ls | grep fix5
