#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/adba6b82bdb9d
test ! -e "$P/71.txt"
first=$(cat "$P/70.txt"); [[ "$first" =~ ^[0-9]+$ ]]
q=$(squeue -j "$first" -h -o '%i' 2>&1 | sed -n '/^[0-9]/p' || true)
test -z "$q"
st=$(TZ=UTC sacct -j "$first" -X -n -P -o State,NodeList | sed -n 1p)
if [[ "${st%%|*}" != COMPLETED ]]; then echo E51 >&2; exit 1; fi
node=${st#*|}
[[ "$node" =~ ^[A-Za-z0-9-]+$ ]]
/usr/bin/python3 -I -s -B "$P/9.py" 2 "$P" 1
q=$(squeue -u jjyeung -p general -h)
test -z "$q"
reply=$(sbatch --parsable --account=mt01 --partition=general --exclude=orchard-community-4 --nodes=1 --ntasks=1 --job-name=a15_cot_apadba6b82bdb9d --gres=gpu:1 --cpus-per-task=16 --mem=200G --time=00:50:00 --no-requeue --export=NONE --chdir=/tmp --nodelist="$node" --output="$P/51.out" --error="$P/51.stderr" --wrap="exec /usr/bin/python3 -I -s -B $P/9.py 1 $P 1")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/71.txt")
printf '%s\n' "$job"
