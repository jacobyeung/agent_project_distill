#!/bin/bash
#SBATCH -A mt01 -p preempt -N1 --ntasks=1 --gres=gpu:8 -c 96 --mem=1600G -t 24:00:00
#SBATCH -J cv8 -o /home/jjyeung/okit/x/b6827881/o/%j.out --no-requeue --signal=B:USR1@900
m=$(/usr/bin/python3 -I /home/jjyeung/okit/x/b6827881/b/r8.py /tmp/jjyeung/okit_8865619b/runs/c1d58a31)
exec /bin/bash /home/jjyeung/okit/x/b6827881/b/r.sh $m 1
