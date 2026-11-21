export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; D=$X/t_7ec7c28925b4; date -u +%TZ
test -e $D && { echo EXISTS; exit 1; }; mkdir -m 700 $D && cd $D && tar xf - && mv rl_t.py t.py && mv rl_run.sh r.sh && chmod 700 r.sh && ls
sbatch -p preempt --gres=gpu:1 --cpus-per-task=4 --mem=32G -t 00:10:00 --no-requeue --job-name=a15_cot_ap7ec7c28925b4 -o $D/s.log -e $D/s.err --wrap "bash $D/r.sh $D"
sleep 50; squeue -u $USER -h -o "%i %P %j %T %M %R"; cat $D/r.txt 2>/dev/null
