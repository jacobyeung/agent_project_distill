#!/bin/bash
#SBATCH -p preempt
#SBATCH -w orchard-community-2
#SBATCH --job-name=a15_cot_ap97f8b3c867
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --no-requeue
#SBATCH --output=/project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap97f8b3c867_%j.log
umask 077
N=/tmp/q_22c714e1_173349; D=/project/community/jjyeung/okh7/x_22c714e1/o/173349
ls -la $N | head -30
for f in q.log 173349.steps; do test -f $N/$f && { s=$(stat -c %s $N/$f); echo "$f $s"; [ "$s" -lt 5000000 ] && cp $N/$f $D/$f; }; done
ls -la $D
