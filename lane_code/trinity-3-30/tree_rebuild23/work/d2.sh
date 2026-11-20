#!/bin/bash
#SBATCH --partition=preempt
#SBATCH --job-name=a15_cot_ap4bdcad7aa313
#SBATCH --nodelist=orchard-flame-29
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --no-requeue
#SBATCH --output=/tmp/q_d2_%j.log
#SBATCH --error=/tmp/q_d2_%j.err
X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/$SLURM_JOB_ID; mkdir -p $O; R=/tmp/q_d2_$SLURM_JOB_ID.txt
{
echo "SLURM_TMPDIR=${SLURM_TMPDIR:-unset} host=$(hostname -s)"; df -h /tmp ${SLURM_TMPDIR:-/tmp} | tail -2
for d in /tmp/q_e2_173911 ${SLURM_TMPDIR:-/tmp}/q_e2_173911; do echo "== $d"; test -d $d && find $d -maxdepth 5 -printf '%M %s %p\n' 2>&1 | head -200; done
D=/tmp/q_e2_173911; test -d $D || D=${SLURM_TMPDIR:-/tmp}/q_e2_173911
if test -d $D; then find $D -maxdepth 6 -type f \( -name '*.log' -o -name '*.jsonl' -o -name '*.err' -o -name '*receipt*' \) -size -1M ! -iname '*sess*' 2>/dev/null | head -40 | while read f; do echo "#### $f"; tail -c 4000 "$f" | sed -E 's#https?://[^ "]*#<url>#g; s#(upload_id|uploadId|token|Authorization)[^ "&,]*#<redacted>#g'; echo; done; fi
echo "== env proxy names"; env | grep -i proxy | sed -E 's#=.*#=<set>#'
echo "== tcp"; timeout 15 python3 -c "import socket,time;t=time.time();s=socket.create_connection(('storage.googleapis.com',443),10);print('tcp ok',round(time.time()-t,3))" 2>&1 | tail -1
echo "== https"; timeout 25 curl -sS -m 20 -o /dev/null -w '%{http_code} %{time_total}\n' https://storage.googleapis.com/ 2>&1 | tail -1
} > $R 2>&1
cp $R $O/d2.txt
