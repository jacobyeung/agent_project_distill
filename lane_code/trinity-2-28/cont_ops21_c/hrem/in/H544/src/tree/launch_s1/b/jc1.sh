#!/bin/bash
#SBATCH -A mt01 -p general -N1 --ntasks=1 --gres=gpu:1 -c 16 --mem=400G -t 04:00:00
#SBATCH -J cv1c -o /home/jjyeung/okit/x/b6827881/o/%j.out
exec /bin/bash /home/jjyeung/okit/x/b6827881/b/r.sh c 1
