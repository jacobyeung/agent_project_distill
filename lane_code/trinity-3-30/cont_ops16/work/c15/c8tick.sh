D=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918
date -u +%TZ
ls -t $D/orch_n30/events/review_h1pkt/ | head -3
ls -t $D/orch_n30/events/cont_ops/ | grep _ORCH_ | head -2
ls -t $D/ | grep INBOX_TO_DISTILL | head -2
ls /scratch/jjyeung/orch_n30/cont_ops/inbox/
tail -2 /scratch/jjyeung/orch_n30/review_h1pkt/STATUS.md
pgrep -f review_h1pkt.md >/dev/null && echo reviewer_alive || echo reviewer_gone
