#!/bin/bash
set +x
set -Eeuo pipefail
D=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
cd "$D"
# One explicit status call; operator controls polling (at most once per minute).
timeout 300 bash "$OSSH" 'bash -s' < pm1.sh
