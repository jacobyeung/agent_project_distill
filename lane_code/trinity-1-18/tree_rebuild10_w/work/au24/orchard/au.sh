#!/bin/bash
#SBATCH -p preempt
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:45:00
#SBATCH --no-requeue
#SBATCH --job-name=JOBNAME_PLACEHOLDER
#SBATCH --signal=TERM@90
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/au_%j.log
#SBATCH --error=/project/community/jjyeung/okh7/x_22c714e1/j/au_%j.err
set -euo pipefail
umask 077
ulimit -c 0
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES=''
K=/project/community/jjyeung/okh7/x_22c714e1/au
W="${SLURM_TMPDIR:-/tmp}/au_${SLURM_JOB_ID:?}"
O="/project/community/jjyeung/okh7/x_22c714e1/o/${SLURM_JOB_ID}"
export TMPDIR="$W/k_0" XDG_CACHE_HOME="$W/k_1" HF_HOME="$W/k_2"
export TORCH_HOME="$W/k_3" TRITON_CACHE_DIR="$W/k_4" MPLCONFIGDIR="$W/k_5"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
nice -n 10 mkdir -p "$TMPDIR" "$XDG_CACHE_HOME" "$O"
cd "$W"
exec nice -n 10 /usr/bin/python3 -I -s -B "$K/au.py" s "$W" "$O"
