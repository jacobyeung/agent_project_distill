# wait up to $1 s for a new ORCH file in cont_ops events or a new RESULT in r1_ops events
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
a=$(ls $E/cont_ops | grep _ORCH_ | sort | tail -1); b=$(ls $E/r1_ops $E/reader_r1 $E/review_h1read4 | grep -E '_RESULT_|_BLOCKER_|VERDICT' | sort | tail -1); c=$(ls /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918 | grep INBOX_TO_DISTILL | sort | tail -1)
for i in $(seq 1 $(( ${1:-570} / 30 ))); do
  sleep 30
  a2=$(ls $E/cont_ops | grep _ORCH_ | sort | tail -1); b2=$(ls $E/r1_ops $E/reader_r1 $E/review_h1read4 | grep -E '_RESULT_|_BLOCKER_|VERDICT' | sort | tail -1); c2=$(ls /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918 | grep INBOX_TO_DISTILL | sort | tail -1)
  [ "$a$b$c" != "$a2$b2$c2" ] && { echo "NEW $(date -u +%TZ): $a2 | $b2 | $c2"; exit 0; }
done; echo "none $(date -u +%TZ) last: $a | $b | $c"
