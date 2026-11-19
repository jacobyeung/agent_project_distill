#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/okh7/a15_cot_apd50ba921ef1f4
test "$(cat "$P/a/1.txt")" = 0
cd "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 02:30:00
test ! -e "$P/a/4.txt"
test ! -e "$P/a/c"
CPU_REPLY=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES=  sbatch --parsable --account=mt01 --partition=preempt --nodes=1 --ntasks=1  --job-name=a15_cot_apd50ba921ef1f4 --cpus-per-task=8 --mem=200G --time=04:00:00  --exclude='orchard-flame-[0-31]' --export=ALL --no-requeue --chdir=/tmp  --output="$P/a/4.log" --error="$P/a/4.err"  --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
CPU_JOB=${CPU_REPLY%%;*}
[[ "$CPU_JOB" =~ ^[0-9]+$ ]]
printf '%s
' "$CPU_JOB" > "$P/a/4.txt"
cat $P/a/4.txt; TZ=UTC squeue -u jjyeung -h -o "%i %j %P %T %M"
