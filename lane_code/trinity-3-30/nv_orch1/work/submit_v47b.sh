set +x; export TZ=UTC; J=/project/community/jjyeung/4f5e45fe5d74c; cd $J
for j in $(squeue -h -u jjyeung -p preempt -o '%i %j' | awk '$2 ~ /^a15_cot_ap/ {print $1}' | grep -x -F -f log/JOBIDS); do scancel $j; echo cancelled $j; done; sleep 8
mv queue/20_v7a.jsonl hold/v7bool/20_v7a.parked && ls queue
export NVO_WORKERS=64
JID=$(sbatch --parsable --account=mt01 --partition=preempt --exclude='orchard-flame-[0-31]' --nodes=1 --ntasks=1 --cpus-per-task=16 --mem=64G --time=20:00:00 --requeue --export=PATH,HOME,USER,NVK_A,NVK_B,NVK_C,NVK_D,NVO_WORKERS --output=$J/log/%j.out --chdir=/tmp --job-name=a15_cot_apbf68d556a6 $J/kit/job.sh 3600 k6)
unset NVK_A NVK_B NVK_C NVK_D
echo $JID >> $J/log/JOBIDS; echo "submitted $JID"
