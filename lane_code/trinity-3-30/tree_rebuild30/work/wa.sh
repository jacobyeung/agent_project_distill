# wait up to 580 s for an ORCH event, an inbox file, or an answer to the N resubmission question
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918; E=$B/orch_n30/events/tree_rebuild; I=/scratch/jjyeung/orch_n30/tree_rebuild30/inbox; A=/data2/jjyeung/agent_project_data/SAVED_USER_QUESTIONS_ANSWERED.md
sig() { ls $E | grep -c '_ORCH_'; ls $I 2>/dev/null | wc -l; grep -c 'tree_rebuild30' $A 2>/dev/null; ls $B | grep -c INBOX_TO_DISTILL; }
s0=$(sig); t=0; until [ $t -ge 580 ] || [ "$(sig)" != "$s0" ]; do sleep 20; t=$((t+20)); done
date -u +%TZ; [ "$(sig)" != "$s0" ] && { echo CHANGED; ls -t $E | head -3; ls -t $I 2>/dev/null | head -3; grep 'tree_rebuild30' $A | tail -1 | cut -c1-400; ls -t $B | grep INBOX_TO_DISTILL | head -2; }
grep 'tree_rebuild30' /data2/jjyeung/agent_project_data/SAVED_USER_QUESTIONS.md | grep -o 'OPEN\|DEFAULT APPLIED[^|]*' | tail -1
true
