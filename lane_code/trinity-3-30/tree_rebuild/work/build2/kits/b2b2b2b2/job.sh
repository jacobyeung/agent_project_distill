#!/bin/bash
#SBATCH --partition=advanced
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --job-name=a15_cot_ap55820d03b79e
#SBATCH --output=o/%j.out
#SBATCH --error=o/%j.err
set -euo pipefail
python3 -B b/a.py . --build-only
exit 1
