#!/bin/bash
set -euo pipefail
umask 077
D=$(cd -- "$(dirname -- "$0")" && pwd)
P=/project/community/jjyeung/okh7/a15_cot_apab0123456789
test ! -e "$P/a/8.txt"
/usr/bin/python3 -I -s -B "$D/check.py" "$P" /project/community/jjyeung/okh7/ae71c903
squeue -u jjyeung -p general -h > "$P/a/9.txt"
test ! -s "$P/a/9.txt"
(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)
JOB_REPLY=$(cd "$P" && /usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 04:30:00)
JOB=${JOB_REPLY%%;*}
[[ "$JOB" =~ ^[0-9]+$ ]]
printf '%s\n' "$JOB" > "$P/a/8.txt"
