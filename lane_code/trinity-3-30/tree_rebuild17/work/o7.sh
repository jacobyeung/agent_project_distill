export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -h -o "%i %P %j %T" | grep -E "24d9b8e2" && { echo QUEUED; exit 1; }
cd $X && sbatch -p advanced -w orchard-community-1 --gres=gpu:4 $X/jd2.sh && sbatch $X/jd2.sh; sleep 20
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"; squeue -p advanced -o "%.10i %.10P %.10u %.8T %.10M %.10l %R" | head
