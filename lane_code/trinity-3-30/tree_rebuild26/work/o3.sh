export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR_20; exit 1; }
sha256sum jn6.sh; [ "$(sha256sum jn6.sh | cut -c1-16)" = 1076bfe97159247e ] || { echo BAD; exit 1; }; chmod 700 jn6.sh
sbatch -p preempt --gres=none --cpus-per-task=2 --mem=4G --time=00:10:00 --job-name=a15_cot_ap01b59a60670f $X/jn6.sh
sleep 50; squeue -u $USER -h -o "%i %P %j %T %M %R"; sacct -u $USER -n -X --starttime now-5minutes -o JobID,JobName%24,State,ExitCode,NodeList | tail -3
