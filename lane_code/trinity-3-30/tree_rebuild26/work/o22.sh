export TZ=UTC; D=/project/community/jjyeung/okh7/x_22c714e1/t_9bd36ab1aed7; date -u +%TZ; squeue -u $USER -h -p general -o '%i'
sbatch -p general --gres=gpu:1 --cpus-per-task=4 --mem=32G -t 00:10:00 --no-requeue --job-name=a15_cot_ap9bd36ab1aed7 -o $D/s.log -e $D/s.err --wrap "bash $D/r.sh $D"
