#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/c8b836b4ae536
test -e "$P/2.json"
test ! -e "$P/a/c/CPU.json"
q=$(squeue -u jjyeung -p preempt -h -o '%j' | grep '^a15_cot_ap' || true)
test -z "$q"
s=$(date +%s)
# A failed earlier check is kept, renamed, never removed.
for n in a/c a/4.out a/4.stderr a/6.txt; do if [ -e "$P/$n" ]; then mv "$P/$n" "$P/$n.$s"; fi; done
reply=$(CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=preempt --exclude=orchard-community-4 --nodes=1 --ntasks=1 --job-name=a15_cot_apc8b836b4ae536 --cpus-per-task=16 --mem=200G --time=03:00:00 --no-requeue --export=NONE --chdir=/tmp --output="$P/a/4.out" --error="$P/a/4.stderr" --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c --seconds 10800")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
(set -C; printf '%s\n' "$job" > "$P/a/6.txt")
printf '%s\n' "$job"
