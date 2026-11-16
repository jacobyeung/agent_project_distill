#!/bin/bash
# one check: orchard queue + new ORCH events + inbox
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/evalx27
cd /scratch/jjyeung/orch_n30/evalx27/work/inv
date -u +%H:%MZ
timeout 120 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < poll2.sh 2>&1 | grep -v "^ *JOBID"
find $E -maxdepth 1 -name '*ORCH*' -newer /scratch/jjyeung/orch_n30/evalx27/work/inv/.last_watch -printf '%f\n' 2>/dev/null
ls /scratch/jjyeung/orch_n30/evalx27/inbox
touch /scratch/jjyeung/orch_n30/evalx27/work/inv/.last_watch
