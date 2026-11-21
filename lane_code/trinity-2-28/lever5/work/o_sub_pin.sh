F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo "project_free=${F}G $(date -u +%FT%TZ)"; [ "$F" -ge 5 ] || { echo "HOLD below 5 GiB floor"; exit 3; }
set -euo pipefail
umask 077
P=/project/community/jjyeung/a3b73b53d92a7
cd "$P"
test ! -e a/r2_174200
mkdir a/r2_174200
for x in 1.lock 2.lock 3.txt 8.txt 9.txt f; do [ -e a/$x ] && mv a/$x a/r2_174200/; done
ls a/r2_174200 | tr '\n' ' '; echo
ulimit -S -f 512
(set -C; : > a/1.lock)
test ! -e a/8.txt
/usr/bin/python3 -I -s -B a/9.py "$P"
CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 00:50:00
squeue -u jjyeung -p general -h > a/9.txt
test ! -s a/9.txt
reply=$(/usr/bin/python3 -I -s -B 3.py submit --gpus 1 --time 00:50:00)
job=${reply%%;*}; [[ "$job" =~ ^[0-9]+$ ]]
scontrol update JobId=$job NodeList=orchard-community-1 && echo "pinned rc=0" || echo "pin rc=$?"
printf '%s\n' "$job" > a/8.txt
echo "job=$job"
TZ=UTC squeue -j $job -h -o "%i %T %r %N %S"; scontrol show job $job | grep -o -E '(ReqNodeList|ExcNodeList|NodeList)=[^ ]*'
