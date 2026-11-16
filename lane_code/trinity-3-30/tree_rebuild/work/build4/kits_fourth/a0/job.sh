#!/bin/bash
#SBATCH --partition=advanced
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --job-name=a15_cot_aped175e4fcde5
#SBATCH --output=o/%j.out
#SBATCH --error=o/%j.err
#SBATCH --signal=B:USR1@3600
set -euo pipefail
export TK_JOB_START="${TK_JOB_START:-$(date +%s)}"
trap 'printf "USR1\n" > o/ee000008' USR1
/usr/bin/python3 -I -s -B b/s.py . t 2>&1 | /usr/bin/python3 -I b/opaque.py
