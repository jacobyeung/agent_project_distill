#!/bin/bash
set -euo pipefail
umask 077
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); [ "$F" -ge 5 ] || { echo E48 >&2; exit 3; }
P=/project/community/jjyeung/ac105d39edf1d
test ! -e "$P/6.txt"
test ! -e "$P/4.json"
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
reply=$(CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=general --exclude=orchard-community-4 --nodes=1 --ntasks=1 --job-name=a15_cot_apac105d39edf1d --cpus-per-task=8 --mem=200G --time=01:00:00 --no-requeue --export=NONE --chdir=/tmp --output="$P/4.out" --error="$P/4.stderr" --wrap="exec /usr/bin/python3 -I -s -B $P/9.py 0 $P")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/6.txt")
printf '%s\n' "$job"
