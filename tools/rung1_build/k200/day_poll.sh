#!/bin/bash
# The lane's one day poller (trinity-0-13, no lanemsg): every 10 min one light login-node action recording the quota,
# the two encode reruns, the pack job and the admitted X arms. When RG1_X_S17_K200 is admitted it submits the world-64 X
# preps and the A1S prep (closure 45279da0). Pack verification lines (PACKED ...) go to the log for the lane to copy
# into the user's block. Log: k200/auto.log. Ends when the preps are queued and the pack job has reported, or at 17:00 PT.
R=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/rung1_build_20261027
PY=/home/jjyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12
D=/scratch/jjyeung/rung1_push/k200
CL=45279da0018c72cf5431905b19ba5f10ff7a1a1cb10df4288cf05869c8e2b8b1
LOG=$D/auto.log
say() { echo "$(date -Is) $*" >> $LOG; }
cd $R/tools || exit 1
say "day poller start"
preps=""; packed=""
for i in $(seq 1 60); do
  [ "$(TZ=America/Los_Angeles date +%H%M)" -ge 1700 ] && { say "day poller cap 17:00 PT"; exit 0; }
  tag=$(printf 'dp%03d' $i)
  $PY -B r1actions.py sh $tag $D/day_status.sh >/dev/null
  for t in 1 2 3 4; do timeout 600 env R1_MIN_INTERVAL=55 $PY -B r1aws.py run >/dev/null 2>&1; ls $R/actions/sent | grep -q "_$tag.json" && break; sleep 70; done
  f=$(grep -l "_$tag BEGIN" $(ls -t $R/polls/poll_*.txt | head -4) 2>/dev/null | head -1)
  out=$([ -n "$f" ] && sed -n "/=== ACTION a_.*_$tag BEGIN/,/END rc/p" "$f")
  say "status: $(echo "$out" | grep -E '^QUOTA|^JOB|^K200ADMITTED|^COUNT' | cut -c1-160 | tr '\n' ' ')"
  if [ -z "$preps" ] && echo "$out" | grep -q "K200ADMITTED RG1_X_S17_K200"; then
    for s in SPEC_K200_X9W64_r2 SPEC_K200_A1SW64_r2; do
      d=$($PY -B r1actions.py spec $D/$s.json); n=$($PY -B r1actions.py sbatch $CL $d 32 240G 3:00:00); preps="$preps $n"
    done
    say "queued X_W64 and A1S preps:$preps (each adds about 8 files)"
  fi
  if [ -z "$packed" ] && echo "$out" | grep -q "^PACK_DONE"; then
    echo "$out" | grep -E "^PACKED|^PACK_FAILED" | while read -r line; do say "$line"; done
    packed=yes; say "pack job reported"
  fi
  [ -n "$preps" ] && [ -n "$packed" ] && { say "day poller done"; exit 0; }
  sleep 530
done
