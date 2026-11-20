#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/ac794e028b16f
test ! -e "$P/6.txt"
test ! -e "$P/4.json"
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
reply=$(CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=general --exclude=orchard-community-4 --nodes=1 --ntasks=1 --job-name=a15_cot_apac794e028b16f --cpus-per-task=8 --mem=20G --time=00:30:00 --no-requeue --export=NONE --chdir=/tmp --output=/dev/null --error=/dev/null --wrap="exec /usr/bin/python3 -I -s -B $P/0.py 0 $P")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/6.txt")
printf '%s\n' "$job"
