#!/bin/bash
#SBATCH -A mt01 -p general -N1 --ntasks=1 --gres=gpu:1 -c 16 --mem=400G -t 06:00:00
#SBATCH -J cv0 -o /home/jjyeung/okit/x/b6827881/o/%j.out
set -e
export TK_JOB_START=$(date +%s)
/bin/bash /home/jjyeung/okit/x/b6827881/b/r.sh p 0
/bin/bash /home/jjyeung/okit/x/b6827881/b/r.sh c 1
