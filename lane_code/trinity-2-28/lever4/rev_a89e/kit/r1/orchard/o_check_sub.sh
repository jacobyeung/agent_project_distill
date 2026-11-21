#!/bin/bash
set -euo pipefail
umask 077
S=$(mktemp /tmp/aa89e8fdab55d42.XXXXXXXX)
cat > "$S" <<'BODY'
#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/a89e8fdab55d4
ulimit -S -f 512
cd "$P"
(set -C; : > a/1.lock)
test ! -e a/8.txt
/usr/bin/python3 -I -s -B a/9.py "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 00:50:00
squeue -u jjyeung -p debug -h -o '%j|%b' > a/9.txt
if grep -Eiq '^a15_cot_ap[^|]*[|].*gpu' a/9.txt; then exit 1; fi
reply=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 00:50:00)
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
printf '%s\n' "$job" > a/8.txt
cat a/8.txt
BODY
nohup setsid bash "$S" > "$S.log" 2>&1 <<'A_EOF' &
A_EOF
printf 'pid=%s log=%s\n' "$!" "$S.log"
