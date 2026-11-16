date -u +%T
grep -n "running\|trin_read" /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md | cut -c1-60,130-260 | head -9
ls /scratch/jjyeung/orch_n30/trin_read/inbox
ls /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/trin_read/ | grep ORCH | tail -2
ls /scratch/jjyeung/orch_n30/trin_read/dl | grep -v withdrawn | tr '\n' ' '; echo
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr '\n' ' '; echo
