export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1; J=173964; D=$X/o/${J}_x
test -e $D && { echo EXISTS; ls $D; exit 1; }; mkdir -m 700 $D
cat > $D/w.sh <<'WS'
N=/tmp/q_22c714e1_173964; L=$N/ev/live; D=$1
echo "$(date -u +%FT%TZ) watcher start on $(hostname)"; ls $N/ev $L 2>&1 | head -20
for i in $(seq 1 330); do
  if test -s $L/v.json && { test -s $L/WAITING_REVIEW.json || test $i -gt 320; }; then sleep 15; break; fi
  sleep 30
done
echo "$(date -u +%FT%TZ) copying (i=$i)"; ls -la $L | head -60
cd $L && for f in $(find . -maxdepth 1 -type f -size -5M -printf '%f\n'); do cp -p "$f" "$D/$f.part" && mv "$D/$f.part" "$D/$f"; done
cd $D && sha256sum $(ls | grep -v '^w\.sh$\|^w\.log$') > SHA256SUMS.live && cd $L && sha256sum -c $D/SHA256SUMS.live 2>&1 | grep -vc ': OK$'
du -sh $D; echo "$(date -u +%FT%TZ) watcher done"
WS
chmod 700 $D/w.sh
nohup timeout 10000 srun --overlap --jobid $J -n1 -c1 --mem=1G bash $D/w.sh $D > $D/w.log 2>&1 < /dev/null &
sleep 20; cat $D/w.log | head -30
