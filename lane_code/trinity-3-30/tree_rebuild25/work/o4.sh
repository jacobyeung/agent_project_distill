export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; D=$X/o/173964_y
F=$(df -BG --output=avail /project/community | tail -1 | tr -dc 0-9); echo FREE_GIB $F; [ "$F" -ge 20 ] || { echo BELOW_FLOOR; exit 1; }
test -e $D && { echo EXISTS; exit 1; }; mkdir -m 700 $D
cat > $D/r.sh <<'RS'
N=/tmp/q_22c714e1_173964; D=$1; cd $D
{ date -u +%FT%TZ; hostname; ls -la /tmp | grep 173964; ls -la $N $N/ev $N/ev/live 2>&1 | head -120; } > ls.txt
for f in /tmp/q_22c714e1_173964.log /tmp/q_22c714e1_173964.err $N/ev/q.log $N/ev/r.log $N/ev/dbb.log $N/ev/q.steps; do test -f $f && tail -c 300000 $f > t_$(basename $f).txt; done
mkdir -p ev live; tot=0
for f in $(find $N/ev -maxdepth 1 -type f -size -1500k -name '*.json' -printf '%p\n' 2>/dev/null) $(find $N/ev/live -maxdepth 1 -type f -size -1500k -printf '%p\n' 2>/dev/null); do
 s=$(stat -c %s $f); [ $((tot+s)) -gt 3500000 ] && { echo SKIP $f $s >> skipped.txt; continue; }
 case $f in */live/*) cp -p $f live/;; *) cp -p $f ev/;; esac; tot=$((tot+s)); done
find . -type f ! -name r.sh ! -name SHA256SUMS -print0 | xargs -0 sha256sum > SHA256SUMS; du -sh .; date -u +%FT%TZ
RS
chmod 700 $D/r.sh
sbatch -p preempt -w orchard-community-4 --gres=none -n1 -c1 --mem=2G -t 00:15:00 --no-requeue --job-name=a15_cot_apa7528e5fc70c -o /dev/null -e /dev/null --wrap "bash $D/r.sh $D > $D/r.log 2>&1"
sleep 45; squeue -u $USER -h -o "%i %P %j %T %M"; cat $D/r.log 2>/dev/null | tail; ls -la $D
