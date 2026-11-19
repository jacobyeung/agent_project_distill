#!/bin/bash
#SBATCH --partition=advanced
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=192G
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:4
#SBATCH --no-requeue
set -euo pipefail
umask 077
ROOT="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
N="${SLURM_TMPDIR:-/tmp}/q_22c714e1_${SLURM_JOB_ID:?}"
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
python3 -I -s -B "$ROOT/b/v.py" "$ROOT"
python3 -I -s -B "$ROOT/b/x.py" "$ROOT" "${1:?}" "$N" 2>&1 | python3 -I -s -B "$ROOT/b/l.py" "$ROOT"
