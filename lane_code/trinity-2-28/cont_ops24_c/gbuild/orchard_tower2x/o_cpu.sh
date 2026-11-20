#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/ae27b6409c13f
test ! -e "$P/6.txt"
test ! -e "$P/4.json"
reply=$(CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --job-name=a15_cot_apae27b6409c13f --cpus-per-task=1 --mem=2G --time=00:05:00 --no-requeue --export=NONE --chdir=/tmp --output=/dev/null --error=/dev/null --wrap="exec /usr/bin/python3 -I -s -B $P/0.py 0 $P")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/6.txt")
printf '%s\n' "$job"
