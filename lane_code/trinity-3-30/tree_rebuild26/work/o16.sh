export TZ=UTC; D=/project/community/jjyeung/okh7/x_22c714e1/t_7ec7c28925b4; date -u +%TZ
sbatch -p preempt --gres=gpu:1 --cpus-per-task=4 --mem=32G -t 00:10:00 --no-requeue --job-name=a15_cot_ap7ec7c28925b4 -o $D/s.log -e $D/s.err --wrap "bash $D/r.sh $D"
sleep 40; squeue -u $USER -h -o "%i %P %j %T %M %R"; cat $D/r.txt 2>/dev/null
