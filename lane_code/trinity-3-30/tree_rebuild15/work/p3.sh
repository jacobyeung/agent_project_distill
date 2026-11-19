W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; free -g | sed -n 2p; nproc; uptime
cat /scratch/jjyeung/orch_n30/tr14_rev24j/VERDICT.md; echo ====; cat $W/w24/work/build24f/REHEARSAL_FIX3_REPORT.md; echo ===; grep -n rehearsal $W/w24/work/build24f/go_rehearsal.sh | head -8
ls $W/w24/work/build24f/ | tr '\n' ' '
tmux new -d -s tr15_reh4 "cd $W/w24 && nice -n 10 bash work/build24f/go_rehearsal.sh > $W/w24/work/build24f/rehearsal_run4.log 2>&1; echo RC=\$? >> $W/w24/work/build24f/rehearsal_run4.log"
sleep 20; tmux ls | grep tr1; tail -5 $W/w24/work/build24f/rehearsal_run4.log
