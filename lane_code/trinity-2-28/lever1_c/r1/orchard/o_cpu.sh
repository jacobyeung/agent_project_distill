#!/bin/bash
set -euo pipefail
umask 077
S=$(mktemp /tmp/aa09fdd101cc931.XXXXXXXX)
cat > "$S" <<'BODY'
#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/a09fdd101cc93
cd "$P"
(set -C; : > a/0.lock)
test ! -e a/c
test ! -e a/4.txt
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 00:40:00
reply=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --job-name=a15_cot_apa09fdd101cc93 --cpus-per-task=16 --mem=200G --time=00:40:00 --exclude=orchard-community-4 --export=ALL --no-requeue --chdir=/tmp --output="$P/a/4.log" --error="$P/a/4.err" --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
printf '%s\n' "$job" > a/4.txt
cat a/4.txt
BODY
nohup setsid bash "$S" > "$S.log" 2>&1 < /dev/null &
printf 'pid=%s log=%s\n' "$!" "$S.log"
