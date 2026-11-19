#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_ktow3
exec /data3/shared/scripts/vnice/vnice.sh timeout --signal=TERM --kill-after=10s 2690s bash scripts/gpu_environment.sh C "$@"
