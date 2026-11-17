# usage: bash wait.sh <minutes>; exits early on a new reader_r1 event, inbox, r1_ops proof RESULT, or tick death
W=/scratch/jjyeung/orch_n30/reader_r1/work
T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918; E=$T/orch_n30/events
fp(){ { ls $E/reader_r1 | grep -v STATUS; ls $E/r1_ops | grep RESULT | grep -i proof; ls $T | grep INBOX_TO_DISTILL_ORCH; ls /scratch/jjyeung/orch_n30/reader_r1/inbox; tmux has-session -t rr1_tick 2>/dev/null && echo a; } | md5sum; }
f0=$(fp)
for i in $(seq 1 $1); do sleep 60; [ "$(fp)" != "$f0" ] && break; done
bash $W/look.sh
