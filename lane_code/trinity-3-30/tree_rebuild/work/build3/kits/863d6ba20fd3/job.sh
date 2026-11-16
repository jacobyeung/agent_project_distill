#!/bin/bash
#SBATCH --partition=advanced
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --job-name=a15_cot_ap726175b46ced
#SBATCH --output=o/%j.out
#SBATCH --error=o/%j.err
set -euo pipefail
exec python3 -B b/e.py . t o/ee000001
