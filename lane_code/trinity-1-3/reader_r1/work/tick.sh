T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918
timeout 120 bash $T/orch_n30/tools/ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/reader_r1/work/q5.sh 2>&1 | tail -5
ls -t $T | grep INBOX_TO_DISTILL_ORCH | head -1
ls -t $T/orch_n30/events/reader_r1 | head -3
ls -t $T/orch_n30/events/tower_redecide | head -3
ls -t $T/orch_n30/events/cont_ops | head -2
ls /scratch/jjyeung/orch_n30/reader_r1/inbox
