#!/bin/bash
#SBATCH --partition=advanced
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=48
#SBATCH --mem=800G
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --job-name=a15_cot_apfa83a523d98a
#SBATCH --output=o/%j.out
#SBATCH --error=o/%j.err
#SBATCH --signal=B:USR1@3600
set -euo pipefail
export TK_JOB_START="${TK_JOB_START:-$(date +%s)}"
/usr/bin/python3 -I -s -B b/s.py . t &
p=$!
c=0
trap 'kill -USR1 "$p"' USR1
while kill -0 "$p" 2>/dev/null; do wait "$p" && break || c=$?; done
exit "$c"
