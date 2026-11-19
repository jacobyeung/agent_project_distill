#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_ap24a9e61c
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=02:00:00
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24a9e61c_%j.log
#SBATCH --error=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24a9e61c_%j.err
set -euo pipefail
umask 077
export Q_MODE=r CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8
export TK_JOB_START="$(date +%s)"
R="$(readlink -f -- "${1:?resolved request required}")"
ROOT="$(readlink -f -- "${2:?kit directory required}")"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
export TMPDIR="$N/tmp" XDG_CACHE_HOME="$N/cache" HF_HOME="$N/cache/hf"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
cd "$N"
nice -n 10 python3 -B -I -s "$ROOT/b/v.py" "$ROOT"
nice -n 10 python3 -B -I -s "$ROOT/b/x.py" "$ROOT" "$R" "$N"
