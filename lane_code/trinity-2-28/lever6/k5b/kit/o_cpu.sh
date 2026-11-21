#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/adba6b82bdb9d
test ! -e "$P/6.txt"
test ! -e "$P/4.json"
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
reply=$(CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=general --exclude=orchard-community-4 --nodes=1 --ntasks=1 --job-name=a15_cot_apadba6b82bdb9d --cpus-per-task=16 --mem=200G --time=00:50:00 --no-requeue --export=NONE --chdir=/tmp --output="$P/4.out" --error="$P/4.stderr" --wrap="exec /usr/bin/python3 -I -s -B $P/9.py 0 $P")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/6.txt")
printf '%s\n' "$job"
