export TZ=UTC
P=/project/community/jjyeung/okh7/d9c35d0a/p/ece5eea1c1ec94e169abf835
sha256sum $P/a.sh $P/a.json
sbatch --nice=200 --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G $P/a.sh
sleep 5
squeue -u $USER -o '%i %j %P %T %M %l %S %Q %y %b' | grep -E "JOBID|ece5eea1c1ec94e169abf835"
J=$(squeue -h -u $USER -n a15_cot_apece5eea1c1ec94e169abf835 -o %i)
scontrol show job $J | grep -E "JobId|TimeLimit|Nice|Partition|TRES|StartTime|Reason|Command"
