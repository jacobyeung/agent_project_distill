export TZ=UTC
# yield rule (ORCH 1359Z): our general read ids in OURS (space-separated); cancel them if a jjy_* job is PENDING on general with QOSMaxJobsPerUserLimit
G=$(squeue -u jjyeung -p general -h -o "%i %j %T %r" 2>&1); echo "$G" | sed 's/^/GEN /'
if [ -n "${OURS:-}" ]; then
  MP=$(echo "$G" | awk '$2 ~ /^jjy_/ && $3=="PENDING" && $4 ~ /QOSMaxJobsPerUser/')
  RUN=""; for j in $OURS; do echo "$G" | awk -v j=$j '$1==j' | grep -q . && RUN="$RUN $j"; done
  if [ -n "$MP" ] && [ -n "$RUN" ]; then scancel $RUN; echo "YIELD_CANCELLED$RUN at $(date -u +%TZ) rc=$? because: $MP"; fi
fi
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
test -s $K/o/$J.err && { echo "== err (filtered)"; grep -v -E 'TORCH_NCCL_AVOID|fast path is not available|Loading weights|barrier\(\)|return func' $K/o/$J.err | tail -n 8 | cut -c1-300; }
R=$K/runs/17c4ffa4; ls $R 2>/dev/null | tr '\n' ' '; echo
M=$R/metrics_$J.jsonl; test -s $M && python3 - $M <<'PY'
import json,sys,math
L=[l for l in open(sys.argv[1]).read().split('\n')[:-1] if l.startswith('{')]
for l in L[-2:]:
    r=json.loads(l); rs=r['ranks']; sm={k:round(sum(x['stream_means'][k] for x in rs)/len(rs),4) for k in rs[0]['stream_means']}
    st=rs[0].get('h1_answer_stop',{}); fin=all(math.isfinite(v) for x in rs for v in x['stream_means'].values())
    print('== metrics rows %d step %s wall %s finite %s %s share %s/%s=%s trig %s' % (len(L), r['step'], round(rs[0]['wall_seconds']), fin, sm, st.get('window_answer_differs'), st.get('window_own'), st.get('window_share') and round(st['window_share'],3), st.get('triggered')))
PY
ls $K/o | grep -E "gcs_17c4ffa4|m100|m200|H1_STOP" | tr '\n' ' '; echo
squeue -u jjyeung -p general -h -o "GEN %i %j %T %M %R" 2>&1
