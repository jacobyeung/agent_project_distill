#!/bin/bash
#SBATCH --partition=advanced
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --job-name=a15_cot_ape7101080a3d2
#SBATCH --output=o/%j.out
#SBATCH --error=o/%j.err
set -euo pipefail
export TK_JOB_START="${TK_JOB_START:-$(date +%s)}"
python3 -B b/e.py . t o/ee000001 2>&1 | python3 -B b/opaque.py
