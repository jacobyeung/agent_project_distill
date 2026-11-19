#!/bin/bash
# Rolling Codex analyst queue for lane swarm_an: at most MAXJ at a time, each a detached codex_local.sh review (gpt-6-astra, high).
# usage: run_queue.sh <queue file: one "<tag>_<id>" prompt stem per line> ; stop file: $W/work/STOP_QUEUE
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
W=/scratch/jjyeung/orch_n30/swarm_an; P=$B/events/swarm_an/prompts; D=$W/work/cx; MAXJ=${MAXJ:-5}
Q=$1; LOG=$W/out/queue.log; pids=()
alive() { local n=0 p; for p in "${pids[@]}"; do kill -0 "$p" 2>/dev/null && n=$((n+1)); done; echo $n; }
gate() {  # IO governor line 4, load, memory
  while :; do
    rate=$(sed -n 4p /data3/jjyeung/orch_n13_20261026/io_governor/STATE.md | grep -oE '[0-9.]+ MB/s weighted' | head -1 | cut -d' ' -f1)
    load=$(cut -d' ' -f1 /proc/loadavg); avail=$(free -g | awk '/^Mem:/{print $7}')
    if awk -v r="${rate:-99}" -v l="$load" -v a="$avail" 'BEGIN{exit !(r<=10 && l<=30 && a>=60)}'; then return 0; fi
    echo "$(date -u +%FT%TZ) gate wait: rate=$rate load=$load avail=$avail" >> $LOG; sleep 300
  done
}
while read -r stem; do
  [ -z "$stem" ] && continue
  [ -f $W/work/STOP_QUEUE ] && { echo "$(date -u +%FT%TZ) STOP_QUEUE present; not launching $stem" >> $LOG; break; }
  while [ "$(alive)" -ge "$MAXJ" ]; do sleep 20; done
  gate
  setsid nohup bash $B/tools/codex_local.sh review $D $P/$stem.md --model gpt-6-astra --effort high --label san_$stem --skip-git-check > $W/out/cx_$stem.log 2>&1 < /dev/null &
  pids+=($!)
  echo "$(date -u +%FT%TZ) launched $stem pid $! rate=$rate load=$load avail=$avail" >> $LOG
  sleep 20
done < "$Q"
while [ "$(alive)" -gt 0 ]; do sleep 30; done
echo "$(date -u +%FT%TZ) queue $Q drained" >> $LOG
