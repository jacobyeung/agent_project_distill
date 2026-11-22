#!/bin/bash
T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools
date -u +%H%MZ
timeout 60 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-0-13.ib 'nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" " "'; echo
timeout 300 bash $T/ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/lever7/work/q3.sh
grep -E 'lever7|\| running' /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md | cut -c1-200 | sort -u
tail -n 2 /scratch/jjyeung/orch_n30/lever7/gtcd/arkit/logs/stage.log
ls /scratch/jjyeung/orch_n30/lever7/inbox; ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/lever | head -2
