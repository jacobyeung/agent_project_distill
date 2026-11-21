#!/bin/bash
set -euo pipefail
umask 077
S=$(mktemp /tmp/aa5d31c07be9f21.XXXXXXXX)
cat > "$S" <<'BODY'
#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/a5d31c07be9f2
ulimit -S -f 512
cd "$P"
(set -C; : > a/0.lock)
test ! -e a/c
test ! -e a/4.txt
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 00:50:00
reply=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 00:50:00 --cpu-only)
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
printf '%s\n' "$job" > a/4.txt
cat a/4.txt
BODY
nohup setsid bash "$S" > "$S.log" 2>&1 <<'A_EOF' &
A_EOF
printf 'pid=%s log=%s\n' "$!" "$S.log"
