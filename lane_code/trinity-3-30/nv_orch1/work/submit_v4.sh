set +x
export TZ=UTC; J=/project/community/jjyeung/4f5e45fe5d74c
cd $J && ls queue; test ! -e queue/40_v4s.jsonl && cp hold/v4/40_v4s_2k.jsonl queue/40_v4s.jsonl && cp hold/v4/41_v4a_2k.jsonl queue/41_v4a.jsonl && sha256sum queue/* kit/nvo_run.py excl/*.pin && test ! -e ctl/STOP
echo 8 > ctl/RATE; echo 24 > ctl/INFLIGHT; echo 3000000 > ctl/BPS; echo 120 > ctl/BUDGET
export NVO_WORKERS=96
JID=$(sbatch --parsable --account=mt01 --partition=preempt --exclude='orchard-flame-[0-31]' --nodes=1 --ntasks=1 --cpus-per-task=16 --mem=48G --time=12:00:00 --requeue --export=PATH,HOME,USER,NVK_A,NVK_B,NVK_C,NVK_D,NVO_WORKERS --output=$J/log/%j.out --chdir=/tmp --job-name=a15_cot_ap32c481b9f2 $J/kit/job.sh 1800 k6)
unset NVK_A NVK_B NVK_C NVK_D
echo $JID >> $J/log/JOBIDS; echo "submitted $JID"; sleep 5; squeue -u jjyeung -o '%i %j %P %T %M %R'
