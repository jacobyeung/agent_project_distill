#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"
: "${GF1_PYTHON:?Set the local training environment interpreter}"
: "${GF1_CONFIG:?Set the prepared, pinned native carrier-c1-run-v1 config}"
: "${GF1_LOG:?Set a new log path on local scratch}"
: "${MASTER_ADDR:?Set the allocated compute node address}"
case "$MASTER_ADDR" in localhost|127.*|::1) echo "Use a compute-node address, not loopback" >&2; exit 2;; esac
export PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 STUDENT_IO_THREADS=1
export XDG_CACHE_HOME="${GF1_CACHE:-/scratch/$USER/.cache}" HF_HOME="${GF1_HF_HOME:-/scratch/$USER/hf}"
export TRITON_CACHE_DIR="${GF1_TRITON_CACHE:-/scratch/$USER/.triton}"
"$GF1_PYTHON" -B - "$GF1_CONFIG" 1 <<'CHECK'
import json,sys
from student_pilot.carrier_c1_run import validate
cfg=json.load(open(sys.argv[1]));stage=int(sys.argv[2]);validate(cfg)
assert cfg['geometry_online']['gf1']['stage']==stage
assert cfg['world_size']==4
assert cfg.get('preparation'), 'Run the native prepare/dryrun and bind its receipt first'
CHECK
# Run under the allocation's existing vnice/Slurm wrapper. This script never obtains a lease.
resume=()
if [[ -n "${GF1_RESUME:-}" ]]; then resume=(--resume "$GF1_RESUME"); fi
exec "$GF1_PYTHON" -B scripts/gf1_stall_guard.py --log "$GF1_LOG" \
  --stall-seconds "${GF1_STALL_SECONDS:-900}" --startup-seconds "${GF1_STARTUP_SECONDS:-3600}" -- \
  "$GF1_PYTHON" -B -m torch.distributed.run --nproc_per_node=4 \
  --master_addr="${MASTER_ADDR}" --master_port="${MASTER_PORT:-29500}" \
  -m student_pilot.carrier_c1_run train --config "$GF1_CONFIG" "${resume[@]}"
