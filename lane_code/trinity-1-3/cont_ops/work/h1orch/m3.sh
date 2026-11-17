export TZ=UTC
K=/project/community/jjyeung/okh7/x_4b3114cf; J=170527; N=${N:-8}
prev=""
for i in $(seq 1 $N); do
  s=$(squeue -j $J -h -o '%T %M' 2>&1)
  t=$(tail -n 1 $K/o/$J.w.steps 2>/dev/null | cut -c1-200); u=$(tail -n 1 $K/o/$J.steps 2>/dev/null | cut -c1-200); e=$(wc -c < $K/o/$J.err 2>/dev/null)
  cur="$s | err=$e | W: $t | S: $u | $(ls $K/o | wc -l) files"
  [ "$cur" != "$prev" ] && echo "$(date -u +%TZ) $cur"
  prev=$cur
  case "$s" in RUNNING*|PENDING*) ;; *) break;; esac
  sleep 30
done
ls $K/o | tr '\n' ' '; echo
test -s $K/o/$J.err && { echo "== err"; tail -n 10 $K/o/$J.err | cut -c1-300; }
