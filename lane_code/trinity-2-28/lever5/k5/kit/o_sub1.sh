#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/a51f1ee88f0c9
test ! -e "$P/71.txt"
first=$(cat "$P/70.txt"); [[ "$first" =~ ^[0-9]+$ ]]
node=$(TZ=UTC sacct -j "$first" -X -n -P -o NodeList | sed -n 1p)
[[ "$node" =~ ^[A-Za-z0-9-]+$ ]]
/usr/bin/python3 -I -s -B "$P/9.py" 2 "$P" 1
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
reply=$(sbatch --parsable --account=mt01 --partition=general --exclude=orchard-community-4 --nodes=1 --ntasks=1 --job-name=a15_cot_apa51f1ee88f0c9 --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=00:50:00 --no-requeue --export=NONE --chdir=/tmp --nodelist="$node" --output="$P/51.out" --error="$P/51.stderr" --wrap="exec /usr/bin/python3 -I -s -B $P/9.py 1 $P 1")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/71.txt")
printf '%s\n' "$job"
