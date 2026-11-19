#!/bin/bash
#SBATCH -p preempt
#SBATCH --job-name=a15_cot_ap24a9e61c
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24a9e61c_%j.log
#SBATCH --error=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24a9e61c_%j.err
set -euo pipefail
umask 077
X=/project/community/jjyeung/okh7/x_22c714e1
echo "$(date -u +%FT%TZ) resolve start"
python3 -I -s -B $X/n/b/resolve.py --pool /project/community/jjyeung/okh7 --listing $X/l.json --output $X/j/r_${SLURM_JOB_ID}.json
echo "$(date -u +%FT%TZ) resolve done"
bash $X/jr.sh $X/j/r_${SLURM_JOB_ID}.json $X/n
echo "$(date -u +%FT%TZ) routing job done"
