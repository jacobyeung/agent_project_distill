set +x
export TZ=UTC; J=/project/community/jjyeung/4f5e45fe5d74c
cd $J && mkdir -p done_q && for q in queue/01_probe.jsonl queue/10_c64.jsonl; do [ -e $q ] && mv $q done_q/; done; ls queue; test ! -e queue/20_v7p.jsonl && mv hold/v7/20_v7p.jsonl queue/ && sha256sum queue/20_v7p.jsonl kit/forms.py kit/nvo_run.py excl/DENY.sha256
echo 8 > ctl/RATE; echo 24 > ctl/INFLIGHT; echo 3000000 > ctl/BPS; echo 260 > ctl/BUDGET
export NVO_WORKERS=96
JID=$(sbatch --parsable --account=mt01 --partition=preempt --exclude='orchard-flame-[0-31]' --nodes=1 --ntasks=1 --cpus-per-task=16 --mem=48G --time=12:00:00 --requeue --export=PATH,HOME,USER,NVK_A,NVK_B,NVK_C,NVK_D,NVO_WORKERS --output=$J/log/%j.out --chdir=/tmp --job-name=a15_cot_ap28a733b683 $J/kit/job.sh 1800 k6)
unset NVK_A NVK_B NVK_C NVK_D
echo $JID >> $J/log/JOBIDS; echo "submitted $JID"; sleep 5; squeue -u jjyeung -o '%i %j %P %T %M %R'
