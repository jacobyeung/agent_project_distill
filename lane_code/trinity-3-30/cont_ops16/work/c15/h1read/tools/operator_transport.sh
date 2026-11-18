#!/bin/bash
# Operator-only entry point; never run by offline tests or kit preparation.
set -euo pipefail
exec bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh "$@"
