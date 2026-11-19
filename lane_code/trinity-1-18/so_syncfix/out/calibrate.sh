#!/bin/bash
# Saved owner script. Invoke with: bash -eu /path/to/so_syncfix/calibrate.sh
date -u
export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1
B=${B:-/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30}
S=${S:-/scratch/jjyeung/distill_sync}
PYTHON=${LCS_OWNER_PYTHON:-/usr/bin/python3}
PKG=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
[ "$(hostname -s)" = trinity-3-30 ] || { echo 'CALIBRATION REFUSED: wrong host' >&2; exit 2; }
[ "${LCS_ROBUST_SYNC:-0}" != 1 ] && [ ! -e "$S/LCS_ROBUST_SYNC" ] && [ ! -L "$S/LCS_ROBUST_SYNC" ] || {
  echo 'CALIBRATION REFUSED: keep robust mode OFF in the hourly loop' >&2; exit 2;
}
[ "$(readlink -f "$S")" = "$S" ] || { echo 'CALIBRATION REFUSED: S has a symlinked ancestor' >&2; exit 2; }
(cd "$B" && nice -n 10 sha256sum -c "$PKG/POSTIMAGE.sha256")
nice -n 10 "$PYTHON" -I -s -B "$PKG/owner_checks.py" pre-enable "$S/sync.log"
# Check immediately before the single run; a refusal never waits or retries.
nice -n 10 "$PYTHON" -I -s -B "$PKG/owner_checks.py" window "$S/sync.log"
nice -n 10 env LCS_B="$B" LCS_S="$S" LCS_ROBUST_SYNC=1 LCS_FILE_SECONDS=3 \
  LCS_SCAN_SECONDS=1800 LCS_COPY_SECONDS=1800 LCS_LEG_SECONDS=1900 \
  LCS_REMOTE_SECONDS=2000 LCS_NODE_SECONDS=2200 LCS_KILL_SECONDS=5 \
  bash "$B/tools/lane_code_sync.sh" --stage-only > "$S/robust_calibration.log" 2>&1 || {
    echo "CALIBRATION FAILED rc=$?; see $S/robust_calibration.log" >&2; exit 2;
  }
nice -n 10 "$PYTHON" -I -s -B "$PKG/calibrate_budgets.py" \
  "$S/robust_calibration.log" "$S/sync.log" > "$S/LCS_ROBUST_BUDGETS.next"
cat "$S/LCS_ROBUST_BUDGETS.next"
mv "$S/LCS_ROBUST_BUDGETS.next" "$S/LCS_ROBUST_BUDGETS"
echo 'CALIBRATION OK; robust mode remains OFF. Review the measurements before creating the flag.'
date -u
