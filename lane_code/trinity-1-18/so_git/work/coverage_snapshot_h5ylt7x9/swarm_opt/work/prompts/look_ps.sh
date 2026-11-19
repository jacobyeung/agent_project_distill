tmux ls 2>&1 | grep so_; for t in so_step so_launch so_read; do tmux has-session -t "=$t" ; echo "$t rc=$?"; tmux has-session -t "$t"; echo "$t plain rc=$?"; done
ps -eo pid,etime,args | grep -E 'codex' | grep -v grep | grep -E 'so_' | cut -c1-200
for t in so_step so_launch; do R=$(ls -d /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/*_$t | tail -1); cat $R/meta.json | head -20; tail -c 1500 $R/transcript.log; echo; done
