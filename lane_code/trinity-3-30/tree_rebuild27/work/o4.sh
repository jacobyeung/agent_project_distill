export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; D=$X/t_e7c1a94b3d20; date -u +%TZ
sbatch -p advanced --gres=gpu:1 --cpus-per-task=4 --mem=32G -t 00:10:00 --no-requeue --job-name=a15_cot_ape7c1a94b3d20 -o $D/s.log -e $D/s.err --wrap "bash $D/r.sh $D $X/n"
sleep 30; squeue -u $USER -h -o "%i %P %j %T %M %R"; ls -la $X/n_s | tail -3; ls $X/n/b | grep -c pycache
