#!/bin/bash
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=800G
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --job-name=a15_cot_ap726175b46ced
#SBATCH --output=o/%j.out
#SBATCH --error=o/%j.err
set -euo pipefail
mkdir -p o/ee000003
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && "${SLURM_GPUS:-0}" == 0 && "${SLURM_JOB_GPUS:-0}" == 0 ]] || exit 2
exec env -i PATH=/usr/bin:/bin TMPDIR="$PWD/o/ee000003" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 python3 -B b/e.py . h o/ee000002
