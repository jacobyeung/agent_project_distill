#!/bin/bash
#SBATCH --job-name=a15_cot_apcbee11a6
#SBATCH --partition=preempt
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=192G
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:1
#SBATCH --no-requeue
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/%j.out
set -euo pipefail
umask 077
X=/project/community/jjyeung/okh7/x_22c714e1
echo "$(date -u +%FT%TZ) resolve start"
python3 -I -s -B $X/q/b/resolve.py --pool /project/community/jjyeung/okh7 --listing $X/l.json --output $X/j/r_${SLURM_JOB_ID}.json
echo "$(date -u +%FT%TZ) resolve done"
bash $X/q/job.sh $X/j/r_${SLURM_JOB_ID}.json
echo "$(date -u +%FT%TZ) job done"
