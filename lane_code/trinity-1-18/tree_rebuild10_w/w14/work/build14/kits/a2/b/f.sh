#!/bin/bash
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=800G
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --job-name=a15_cot_ap49801157088e
#SBATCH --output=o/%j.out
#SBATCH --error=o/%j.err
set -euo pipefail
mkdir -p o/ee000003
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && "${SLURM_GPUS:-0}" == 0 && "${SLURM_JOB_GPUS:-0}" == 0 && "${SLURM_GPUS_PER_NODE:-0}" == 0 && -z "${CUDA_VISIBLE_DEVICES:-}" ]] || exit 2
env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B b/s.py . h 2>&1 | /usr/bin/python3 -I b/opaque.py
