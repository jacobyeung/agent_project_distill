#!/bin/bash
#SBATCH -p preempt
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --job-name=JOBNAME_PLACEHOLDER
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/%j.log
#SBATCH --error=/project/community/jjyeung/okh7/x_22c714e1/j/%j.err
set -euo pipefail
umask 077
ROOT=/project/community/jjyeung/okh7/x_22c714e1/qd
H=/project/community/jjyeung/okh7/x_22c714e1/rcj
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
mkdir "$N"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"
export HF_HOME="$N/cache/hf" TORCH_HOME="$N/cache/torch" TRITON_CACHE_DIR="$N/cache/triton" MPLCONFIGDIR="$N/cache/plot"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd "$ROOT"
finish() {
    local rc="$?"
    trap - EXIT
    nice -n 10 python3 -I -s -B "$H/x.py" publish "$ROOT" "$N" "$SLURM_JOB_ID" "$rc" || exit 1
    exit "$rc"
}
trap finish EXIT
nice -n 10 python3 -I -s -B "$H/x.py" stage "$ROOT" "$N" "$SLURM_JOB_ID" 2>&1 | nice -n 10 python3 -I -s -B "$ROOT/b/l.py" "$ROOT"
nice -n 10 python3 -I -s -B "$H/x.py" launch "$ROOT" "$N" "$SLURM_JOB_ID" 2>&1 | nice -n 10 python3 -I -s -B "$ROOT/b/l.py" "$ROOT"
