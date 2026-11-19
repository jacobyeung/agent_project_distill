#!/bin/bash
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=192G
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:1
#SBATCH --no-requeue
#SBATCH --output=/tmp/q_%j.log
#SBATCH --error=/tmp/q_%j.err
export PYTHONDONTWRITEBYTECODE=1
set -euo pipefail
umask 077
R="$(readlink -f -- "${1:?E87}")" || { echo E87 >&2; exit 1; }
[[ -f "$R" ]] || { echo E87 >&2; exit 1; }
ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache"
export HF_HOME="$N/cache/hf" TORCH_HOME="$N/cache/torch" TRITON_CACHE_DIR="$N/cache/triton"
export CUDA_CACHE_PATH="$N/cache/cu" MPLCONFIGDIR="$N/cache/plot"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd "$N"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
python3 -B -I -s -B "$ROOT/b/v.py" "$ROOT"
python3 -B -I -s -B "$ROOT/b/x.py" "$ROOT" "$R" "$N" 2>&1 | python3 -B -I -s -B "$ROOT/b/l.py" "$ROOT"
