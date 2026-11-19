#!/bin/bash
# Saved owner script. Invoke only after reviewing calibration: bash -eu /path/to/so_syncfix/enable.sh
date -u
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
B=${B:-/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30}
S=${S:-/scratch/jjyeung/distill_sync}
PYTHON=${LCS_OWNER_PYTHON:-/usr/bin/python3}
PKG=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
[ "$(hostname -s)" = trinity-3-30 ] || { echo 'ENABLE REFUSED: wrong host' >&2; exit 2; }
exec 8>"$S/.sync.lock"
flock -n 8 || { echo 'ENABLE REFUSED: sync holds lock' >&2; exit 3; }
(cd "$B" && nice -n 10 sha256sum -c "$PKG/POSTIMAGE.sha256")
nice -n 10 "$PYTHON" -I -s -B "$PKG/owner_checks.py" pre-enable "$S/sync.log"
nice -n 10 "$PYTHON" -I -s -B "$PKG/calibrate_budgets.py" "$S/robust_calibration.log" > "$S/LCS_ROBUST_BUDGETS.verify"
cmp "$S/LCS_ROBUST_BUDGETS.verify" "$S/LCS_ROBUST_BUDGETS"
[ ! -e "$S/LCS_ROBUST_SYNC" ] && [ ! -L "$S/LCS_ROBUST_SYNC" ] || { echo 'ENABLE REFUSED: flag already exists' >&2; exit 2; }
[ ! -L "$S/LCS_ROBUST_SYNC.next" ] && { [ ! -e "$S/LCS_ROBUST_SYNC.next" ] || [ -f "$S/LCS_ROBUST_SYNC.next" ]; } || {
  echo 'ENABLE REFUSED: pending flag is not regular' >&2; exit 2;
}
umask 077
: > "$S/LCS_ROBUST_SYNC.next"
mv "$S/LCS_ROBUST_SYNC.next" "$S/LCS_ROBUST_SYNC"
echo 'ENABLED: the next hourly invocation reads the flag; check its STAGED, COPIED, push verification and END lines.'
date -u
