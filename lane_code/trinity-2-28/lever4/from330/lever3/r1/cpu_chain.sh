L=/tmp/aa6f198d3c7b200.lwSxw548.log; cat $L | tail -c 600; echo
grep -q '"verified": true' $L || { echo "NOT VERIFIED YET"; exit 4; }
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo "project_free=${F}G $(date -u +%FT%TZ)"; [ "$F" -ge 15 ] || { echo "HOLD below 15 GiB floor"; exit 3; }
TZ=UTC squeue -u $USER -h -p general -o '%i %j %P %T'
#!/bin/bash
set -euo pipefail
umask 077
S=$(mktemp /tmp/aa6f198d3c7b201.XXXXXXXX)
cat > "$S" <<'BODY'
#!/bin/bash
set -euo pipefail
umask 077
P=/project/community/jjyeung/a6f198d3c7b20
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
