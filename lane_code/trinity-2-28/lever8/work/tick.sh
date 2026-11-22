#!/bin/bash
T=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools
date -u +%H%MZ
timeout 300 bash $T/ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/lever8/work/q3.sh
ls /scratch/jjyeung/orch_n30/lever8/inbox; ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/lever | head -3
