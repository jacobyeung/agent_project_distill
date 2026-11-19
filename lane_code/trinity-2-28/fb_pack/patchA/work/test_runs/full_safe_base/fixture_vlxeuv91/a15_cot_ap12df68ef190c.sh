#!/bin/bash
#SBATCH --job-name=a15_cot_ap12df68ef190c
#SBATCH --partition=cpu
#SBATCH --qos=cpu-normal
#SBATCH --time=01:30:00
#SBATCH --array=0-6%4
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=/store/abcd1234/o/a15_cot_ap12df68ef190c_%A_%a.out
set -euo pipefail
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /store/abcd1234/c
"${PYTHON:?}" -B -m student_pilot.recording_pose stage --plan /store/abcd1234/abcd.json --plan-sha256 e0cddc0a7ca2ff606035295b6de17721b7fc9c23b89767bc4165533f168586de --frame-root /store/abcd1234/f --shards 7 --shard "$SLURM_ARRAY_TASK_ID" --output /store/abcd1234/o/"$SLURM_ARRAY_TASK_ID".json
