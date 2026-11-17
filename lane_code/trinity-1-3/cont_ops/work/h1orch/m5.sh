export TZ=UTC
K=/project/community/jjyeung/okh7/x_3fdda0fb; J=170710; N=${N:-8}
prev=""
for i in $(seq 1 $N); do
  s=$(squeue -j $J -h -o '%T %M' 2>&1)
  t=$(tail -n 1 $K/o/$J.w.steps 2>/dev/null | cut -c1-200); u=$(tail -n 1 $K/o/$J.steps 2>/dev/null | cut -c1-200); e=$(cat $K/o/$J.err 2>/dev/null | wc -c)
  cur="$s | err=$e | W: $t | S: $u | $(ls $K/o | wc -l) files"
  [ "$cur" != "$prev" ] && echo "$(date -u +%TZ) $cur"
  prev=$cur
  case "$s" in RUNNING*|PENDING*) ;; *) break;; esac
  sleep 30
done
squeue -j $J -h -o "%T %r start=%S node=%N" 2>&1; sinfo -p advanced -h -o "%t %D" 2>&1 | tr "\n" ";"; echo
ls $K/o | tr '\n' ' '; echo
for f in $K/o/$J.w.steps $K/o/$J.steps; do test -s $f && { echo "== $f"; tail -n 4 $f | cut -c1-250; }; done
test -s $K/o/$J.err && { echo "== err"; tail -n 8 $K/o/$J.err | cut -c1-300; }
R=$K/runs/17c4ffa4; ls $R 2>/dev/null | tr '\n' ' '; echo
M=$R/metrics_$J.jsonl; test -s $M && { echo "== metrics rows $(wc -l < $M)"; tail -n 2 $M | cut -c1-700; }
ls $K/o | grep -E "gcs_17c4ffa4|m100|m200|H1_STOP" | tr '\n' ' '; echo
