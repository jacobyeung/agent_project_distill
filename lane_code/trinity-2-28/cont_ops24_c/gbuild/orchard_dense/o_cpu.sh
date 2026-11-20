#!/bin/bash
set -euo pipefail
umask 077
S=$(mktemp /tmp/aa2ae13e5ef0051.XXXXXXXX)
cat > "$S" <<'BODY'
#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/a2ae13e5ef005
cd "$P"
(set -C; : > a/0.lock)
test ! -e a/c
test ! -e a/4.txt
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 05:00:00
reply=$(env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" CUDA_VISIBLE_DEVICES= sbatch --parsable --account=mt01 --partition=general --nodes=1 --ntasks=1 --job-name=a15_cot_apa2ae13e5ef005 --cpus-per-task=8 --mem=200G --time=05:00:00 --exclude='orchard-flame-[0-31]' --export=ALL --no-requeue --chdir=/tmp --output="$P/a/4.log" --error="$P/a/4.err" --wrap="exec /usr/bin/python3 -I -s -B $P/a/5.py --package $P --sequence $P/a/6.py --results $P/a/c")
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
printf '%s\n' "$job" > a/4.txt
cat a/4.txt
BODY
nohup setsid bash "$S" > "$S.log" 2>&1 < /dev/null &
printf 'pid=%s log=%s\n' "$!" "$S.log"
