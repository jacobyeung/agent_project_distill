#!/bin/bash
# orch.sh <driver> [args...]: run a drv_cp driver on Orchard (one ossh call), filtered of the host-key banner; output also to xfer/<driver>.out
D=/scratch/jjyeung/orch_n30/r1_ops6/rec/r1_ops/work/drv_cp; f=$1; shift
timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh "bash -s -- $*" < "$D/$f" 2>&1 | grep -v -E "^@|WARNING: REMOTE|POSSIBLE|eavesdropping|host key|fingerprint|SHA256:lXw|contact your|google_compute_known|Offending|authentication is disabled" | tee /scratch/jjyeung/orch_n30/r1_ops6/work/xfer/${f%.sh}.out
