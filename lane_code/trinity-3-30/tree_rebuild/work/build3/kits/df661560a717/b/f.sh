#!/bin/bash
#SBATCH --partition=general
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=800G
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --job-name=a15_cot_apeb4df2216101
#SBATCH --output=o/%j.out
#SBATCH --error=o/%j.err
set -euo pipefail
mkdir -p o/ee000003
[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && "${SLURM_GPUS:-0}" == 0 && "${SLURM_JOB_GPUS:-0}" == 0 && "${SLURM_GPUS_PER_NODE:-0}" == 0 && -z "${CUDA_VISIBLE_DEVICES:-}" ]] || exit 2
env -i PATH=/usr/bin:/bin TMPDIR="$PWD/o/ee000003" XDG_CACHE_HOME="$PWD/o/ee000003/c1" HF_HOME="$PWD/o/ee000003/c2" TORCH_HOME="$PWD/o/ee000003/c3" HF_HUB_OFFLINE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 python3 -B b/e.py . h o/ee000002 2>&1 | env -i PATH=/usr/bin:/bin python3 -B b/opaque.py
