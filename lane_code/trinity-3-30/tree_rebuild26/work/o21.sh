export TZ=UTC; D=/project/community/jjyeung/okh7/x_22c714e1/t_b47e5e2141d3; date -u +%TZ
sbatch -p general --gres=gpu:1 --cpus-per-task=4 --mem=32G -t 00:10:00 --no-requeue --job-name=a15_cot_apb47e5e2141d3 -o $D/s.log -e $D/s.err --wrap "bash $D/r.sh $D"
sleep 60; squeue -u $USER -h -o "%i %P %j %T %M %R"; cat $D/r.txt 2>/dev/null | cut -c1-400
