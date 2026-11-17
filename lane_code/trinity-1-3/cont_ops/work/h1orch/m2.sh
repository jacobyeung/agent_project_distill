export TZ=UTC
K=/project/community/jjyeung/okh7/x_4b3114cf; J=170527
prev=""
for i in $(seq 1 8); do
  s=$(squeue -j $J -h -o '%T %M %N %R' 2>&1); f=$(ls $K/o 2>/dev/null | tr '\n' ' ')
  cur="$s | $f"
  [ "$cur" != "$prev" ] && echo "$(date -u +%TZ) $cur"
  prev=$cur
  case "$s" in PENDING*) ;; *) break;; esac
  sleep 30
done
date -u +%TZ
for f in $K/o/$J.err $K/o/$J.w.steps $K/o/$J.steps; do test -f $f && { echo "== $f"; tail -n 8 $f | cut -c1-300; }; done
sacct -j $J -X -n -o State,ExitCode,Start,NodeList%30 2>&1
