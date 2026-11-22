#!/bin/bash
# Stop the rehearsal of job $A15_JOB (default 174246) at once and prove it: TERM then KILL to its driver,
# its process group and every process whose environment carries A15_RUN=<its run folder>; then ps and
# nvidia-smi. Touches nothing of the job and clears nothing (the save sink stays). usage: stop.sh [run folder] (default: the latest run)
export TZ=UTC
JOB=${A15_JOB:-174246}; D=${A15_D:-/tmp/a15_rh_$JOB}
RUN=$(readlink -f "${1:-$D/last}"); LOG=$RUN/log
[[ -d "$RUN" && "$RUN" == "$D"/run_* ]] || { echo "no run folder under $D"; exit 2; }
say() { echo "$(date -u +%FT%TZ) stop.sh: $*" | tee -a "$LOG/go.log"; }
marked() { local p; for p in /proc/[0-9]*; do [[ -O "$p" ]] || continue; tr '\0' '\n' 2>/dev/null < "$p/environ" | grep -qx "A15_RUN=$RUN" && echo "${p#/proc/}"; done; }
drv=$(pgrep -u "$(id -u)" -f "bash $D/rh/go.sh" | tr '\n' ' ')
pg=$(cat "$LOG/pgid" 2>/dev/null); pl=$(cat "$LOG/plan.pgid" 2>/dev/null)
say "driver [$drv] group [$pg] marked [$(marked | tr '\n' ' ')]"
[[ -n "$drv" ]] && kill -TERM $drv 2>/dev/null          # the driver's trap runs its own cleanup
[[ -n "$pg" ]] && kill -TERM -- "-$pg" 2>/dev/null
[[ -n "$pl" ]] && kill -TERM -- "-$pl" 2>/dev/null       # the planner's group (up.py, sw.py)
left=$(marked | tr '\n' ' '); [[ -n "$left" ]] && kill -TERM $left 2>/dev/null
sleep 15
left=$(marked | tr '\n' ' '); [[ -n "$left" ]] && { say "KILL [$left]"; kill -KILL $left 2>/dev/null; }
[[ -n "$pg" ]] && kill -KILL -- "-$pg" 2>/dev/null
[[ -n "$pl" ]] && kill -KILL -- "-$pl" 2>/dev/null
smi=$(cat "$LOG/smi.pid" 2>/dev/null); [[ -n "$smi" ]] && grep -q nvidia-smi "/proc/$smi/cmdline" 2>/dev/null && kill "$smi"
sleep 3
say "proof: marked left [$(marked | tr '\n' ' ')]; driver left [$(pgrep -u "$(id -u)" -f "bash $D/rh/go.sh" | tr '\n' ' ')]"
ps -u "$(id -u)" -o pid,etime,args --width 200 | grep -F "$D" | grep -v -e grep -e "stop.sh" -e ' ps '
say "proof: gpus $(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr '\n' ';') apps [$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr '\n' ';')]"
