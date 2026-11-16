export TZ=UTC
if [ $(date -u +%s) -gt $(date -u -d 2026-11-16T15:20:00Z +%s) ]; then echo "FAIL past 15:20Z cutoff"; exit 5; fi
P=/project/community/jjyeung/okh7/d9c35d0a/p/d627d31523064791d2ce3456
echo "general check (own jobs):"; squeue -p general -h -u $USER -o '%i %j %T %l %e'; if [ -n "$(squeue -p general -h -u $USER -o %i)" ]; then echo "FAIL own job on general"; exit 4; fi; echo "general all users:"; squeue -p general -h -o '%i %u %T' | wc -l
NOW=$(date -u +%s); END=$(date -u -d 2026-11-16T17:35:00Z +%s); MIN=$(( (END-NOW)/60 ))
TL=$(printf '%02d:%02d:00' $((MIN/60)) $((MIN%60))); echo "time limit $TL"
sbatch --nice=200 --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time=$TL $P/a.sh
sleep 5
J=$(squeue -h -u $USER -n a15_cot_apd627d31523064791d2ce3456 -o %i); echo "job $J"
scontrol show job $J | grep -E "JobId|JobState|TimeLimit|Nice|ReqTRES|StartTime"
