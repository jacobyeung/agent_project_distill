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
python3 -B -I -s "$ROOT/b/resolve.py" --pool "/project/community/jjyeung/okh7" --output "$N/r0.json" 2>&1 | python3 -B -I -s "$ROOT/b/l.py" "$ROOT" > "$N/q.log"
setsid bash -c 'set -o pipefail; python3 -B -I -s "$1/b/x.py" "$1" "$2" "$3" 2>&1 | python3 -B -I -s "$1/b/l.py" "$1"' bash "$ROOT" "$N/r0.json" "$N" &
TK_WORK_PID=$!
wait "$TK_WORK_PID"
