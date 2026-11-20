#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/ae63d9b7124fc
test ! -e "$P/7.txt"
/usr/bin/python3 -I -s -B "$P/9.py" 2 "$P"
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
reply=$(sbatch --parsable --account=mt01 --partition=general --exclude=orchard-community-4 --nodes=1 --ntasks=1 --job-name=a15_cot_apae63d9b7124fc --gres=gpu:1 --cpus-per-task=8 --mem=200G --time=00:30:00 --no-requeue --export=NONE --chdir=/tmp --output="$P/5.out" --error="$P/5.stderr" "$P/BATCH.sh")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/7.txt")
printf '%s\n' "$job"
