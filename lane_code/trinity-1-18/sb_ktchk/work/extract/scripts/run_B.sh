#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
exec /data3/shared/scripts/vnice/vnice.sh timeout --signal=TERM --kill-after=10s 10790s bash scripts/gpu_environment.sh B "$@"
