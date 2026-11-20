#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/ae27b6409c13f
test ! -e "$P/7.txt"
/usr/bin/python3 -I -s -B "$P/0.py" 2 "$P"
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
reply=(sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --job-name=a15_cot_apae27b6409c13f)
reply=$(sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --job-name=a15_cot_apae27b6409c13f --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=00:30:00 --no-requeue --export=NONE --chdir=/tmp --output=/dev/null --error=/dev/null "$P/BATCH.sh")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/7.txt")
printf '%s\n' "$job"
