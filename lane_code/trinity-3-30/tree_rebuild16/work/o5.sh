export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep -E "24d9b8e2" && { echo QUEUED; exit 1; }
cd $X && sbatch $X/jd2.sh; sleep 30; squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R" | grep -E "24d9b8e2|JOBID"; sinfo -p preempt -h -o "%n %G %t %C" | head
