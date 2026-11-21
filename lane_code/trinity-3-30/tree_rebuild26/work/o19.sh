export TZ=UTC; D=/project/community/jjyeung/okh7/x_22c714e1/t_34c11e8cc527; date -u +%TZ; scancel 174088; sleep 2
sbatch -p general --gres=gpu:1 --cpus-per-task=4 --mem=32G -t 00:10:00 --no-requeue --job-name=a15_cot_ap34c11e8cc527 -o $D/s.log -e $D/s.err --wrap "bash $D/r.sh $D"
sleep 30; squeue -u $USER -h -o "%i %P %j %T %M %R"
