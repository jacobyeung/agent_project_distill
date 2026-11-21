#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/adba6b82bdb9d
test ! -e "$P/70.txt"
/usr/bin/python3 -I -s -B "$P/9.py" 2 "$P" 0
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
reply=$(sbatch --parsable --account=mt01 --partition=general --exclude=orchard-community-4 --nodes=1 --ntasks=1 --job-name=a15_cot_apadba6b82bdb9d --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=00:50:00 --no-requeue --export=NONE --chdir=/tmp --output="$P/50.out" --error="$P/50.stderr" --wrap="exec /usr/bin/python3 -I -s -B $P/9.py 1 $P 0")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/70.txt")
printf '%s\n' "$job"
