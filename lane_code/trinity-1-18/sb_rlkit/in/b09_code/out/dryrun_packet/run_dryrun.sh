#!/bin/bash
# RL kit dry run: 200 prompts x 8 draws on ONE 48 GB card for at most one hour. Needs ORCH GO + a card.
# Usage: bash run_dryrun.sh SAMPLER.json POOL.jsonl RUN_DIR GPU_INDEX
# Before launch (LANE_RULES): two nvidia-smi readings 5+ minutes apart showing GPU_INDEX empty, in the launch event.
# Off trinity-0-13 the command runs under vnice. Resumable: rerun the same command after a stop (same RUN_DIR).
set -euo pipefail
CFG=$1; POOL=$2; RUN=$3; GPU=$4
L=/scratch/jjyeung/orch_n30/b09_rlkit
PY=${PY:-/scratch/jjyeung/envs/p1cpu/bin/python}
export CUDA_VISIBLE_DEVICES=$GPU PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$L
export XDG_CACHE_HOME=/scratch/$USER/.cache HF_HOME=/scratch/$USER/hf TRITON_CACHE_DIR=/scratch/$USER/.triton
mkdir -p "$RUN"
case "$POOL" in /scratch/*) ;; *) echo "pool must be on /scratch" >&2; exit 2;; esac
case "$RUN" in /scratch/*) ;; *) echo "run dir must be on /scratch" >&2; exit 2;; esac
$PY - "$CFG" "$(dirname "$0")/FORCING.json" "$RUN/SAMPLER.json" <<'PYEOF'
import json, sys
cfg = json.load(open(sys.argv[1])); cfg['forcing'] = json.load(open(sys.argv[2]))
bad = [s for s in ('<EXPORT', '<KIT_CONFIG', '<sha256>', '<RUN_DIR>') if s in json.dumps(cfg)]
if bad: sys.exit('fill the template placeholders: %s' % bad)
json.dump(cfg, open(sys.argv[3], 'w'), indent=1, sort_keys=True)
PYEOF
VNICE=""; [ "$(hostname -s)" != trinity-0-13 ] && VNICE=/data3/shared/scripts/vnice/vnice.sh
cd $L
$VNICE $PY -m rlkit.sampler --config "$RUN/SAMPLER.json" --prompts "$POOL" --out "$RUN" --max-seconds 3300 --limit 200 \
  2>&1 | tee -a "$RUN/sampler.log"
$PY "$(dirname "$0")/measure.py" "$RUN" "$POOL" "$(dirname "$0")/REWARD.json" | tee "$RUN/DRYRUN_MEASURE.json"
