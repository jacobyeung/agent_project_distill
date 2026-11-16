export TZ=UTC
P=/project/community/jjyeung/okh7/d9c35d0a/p/8f7817fb16bc218af285dc61
echo "general check:"; squeue -p general -h -o '%i %u %j %T %l %e' | head -20
NOW=$(date -u +%s); END=$(date -u -d 2026-11-16T16:30:00Z +%s); MIN=$(( (END-NOW)/60 ))
TL=$(printf '%02d:%02d:00' $((MIN/60)) $((MIN%60))); echo "time limit $TL"
sbatch --nice=200 --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=$TL $P/a.sh
sleep 5
J=$(squeue -h -u $USER -n a15_cot_ap8f7817fb16bc218af285dc61 -o %i); echo "job $J"
scontrol show job $J | grep -E "JobId|JobState|TimeLimit|Nice|ReqTRES|StartTime"
