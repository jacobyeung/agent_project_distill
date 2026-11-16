#!/usr/bin/env bash
#SBATCH -A mt01
#SBATCH -p preempt
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=00:40:00
#SBATCH -o /project/community/jjyeung/official_reads/logs/%x_%j.out
O=/project/community/jjyeung/official_reads
mkdir -p /tmp/jjy_vcheck_$SLURM_JOB_ID
python3 -I $O/bin/vcheck.py $O/tree $O/vview $O/VCHECK.json
