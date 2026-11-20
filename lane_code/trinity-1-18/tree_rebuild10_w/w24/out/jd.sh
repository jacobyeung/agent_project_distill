#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_ap24d9b8e2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --signal=B:TERM@600
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24d9b8e2_%j.log
#SBATCH --error=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24d9b8e2_%j.err
set -euo pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
export TK_JOB_START="$(date +%s)"
ROOT="/project/community/jjyeung/okh7/x_22c714e1/qd"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
source "$ROOT/b/ep.sh"
tk_db_loop() {
    local node="$1" output="$2" helper="$3" attempt
    for ((attempt=1; attempt<=180; attempt++)); do
        if [[ -f "$output/routing_selection.json" ]]; then
            if python3 -B -I -s "$helper" "$node" "$output"; then return 0; fi
        fi
        if (( attempt < 180 )); then sleep 60; fi
    done
    return 1
}

export -f tk_db_loop
setsid bash -c 'tk_db_loop "$1" "$2" "$3"' bash "$N" "/project/community/jjyeung/okh7/x_22c714e1/o/$SLURM_JOB_ID" "/project/community/jjyeung/okh7/x_22c714e1/dbb2.py" &
TK_DB_PID=$!
tk_discovery_finish() {
    local status="$1" signal_mode="${2:-}"
    if [[ -n "${TK_DB_PID:-}" ]]; then
        kill -TERM -- "-$TK_DB_PID" 2>/dev/null || true
        wait "$TK_DB_PID" 2>/dev/null || true
    fi
    tk_evidence_finish "$status" "$signal_mode"
}
trap 'tk_discovery_finish $?' EXIT
trap 'tk_discovery_finish 143 signal' TERM
trap 'tk_discovery_finish 138 signal' USR1
python3 -B -I -s "$ROOT/b/resolve.py" --pool "/project/community/jjyeung/okh7" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT" > "$N/q.log"
setsid bash -c 'set -o pipefail; python3 -B -I -s "$1/b/x.py" "$1" "$2" "$3" 2>&1 | python3 -B -I -s "$1/b/l.py" "$1"' bash "$ROOT" "$N/r0.json" "$N" &
TK_WORK_PID=$!
wait "$TK_WORK_PID"
