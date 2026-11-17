T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918
E=$T/orch_n30/events
date -u +%H%MZ; echo "tick:"; sed -n 2,3p /scratch/jjyeung/orch_n30/reader_r1/work/tick_last.txt; head -1 /scratch/jjyeung/orch_n30/reader_r1/work/tick_last.txt
echo "rr1: $(ls -t $E/reader_r1 | grep -v STATUS | head -1)"
echo "r1_ops: $(ls -t $E/r1_ops | grep -v STATUS | head -2 | tr '\n' ' ')"
echo "rev: $(ls $E/review_rr2room | head -3 | tr "\n" " ")"
echo "cont_ops: $(ls -t $E/cont_ops | grep -v STATUS | head -2 | tr '\n' ' ')"
echo "inbox: $(ls -t $T | grep INBOX_TO_DISTILL_ORCH | head -1) lane-inbox: $(ls /scratch/jjyeung/orch_n30/reader_r1/inbox)"
tmux has-session -t rr1_tick 2>/dev/null && echo tick-alive || echo TICK-DEAD
