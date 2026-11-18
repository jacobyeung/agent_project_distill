cd /scratch/jjyeung/orch_n30/cont_ops/work; date -u +%TZ
grep -E 'GEN|YIELD|== metrics|gcs_17c4ffa4|H1_STOP|RUNNING [0-9]' h1orch/m5.out | tail -5 | cut -c1-220
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events; ls -t $E/cont_ops | head -2; ls $E/review_h1eval 2>/dev/null; ls /scratch/jjyeung/orch_n30/cont_ops/inbox
ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918 | grep INBOX_TO_DISTILL | head -1
