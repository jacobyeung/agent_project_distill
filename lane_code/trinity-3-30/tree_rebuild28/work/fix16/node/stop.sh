#!/bin/bash
# fix16: stop walk w1 and everything it started, then prove it. usage: stop.sh [reason]
# Marked processes = every process of mine whose environment carries A15_RUN=<run folder> (set only inside
# the walk's sandbox). Writes only under /tmp/a15_f16_174198.
set -u
export TZ=UTC
D=/tmp/a15_f16_174198; RUN=$D/w1; LOG=$RUN/log/stop.log
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
me=$(id -u)
marked() { local p; for p in /proc/[0-9]*; do [[ -O "$p" ]] || continue; tr '\0' '\n' 2>/dev/null < "$p/environ" | grep -qx "A15_RUN=$RUN" && echo "${p#/proc/}"; done; }
TO=$(pgrep -u "$me" -f '^/usr/bin/timeout -s TERM -k 30 [0-9]+ bash /tmp/a15_f16_174198/n/go.sh w1 NS$' | head -1)
GO=$(pgrep -u "$me" -f '^bash /tmp/a15_f16_174198/n/go.sh w1 NS$' | head -1)
say "stop (${1:-manual}): timeout pid [${TO}] go.sh pid [${GO}] marked [$(marked | tr '\n' ' ')] rc file [$(cat "$RUN/log/rc" 2>/dev/null)]"
left=$(marked | tr '\n' ' ')
if [[ -n "$left" ]]; then kill -TERM $left 2>/dev/null; sleep 8; fi
left=$(marked | tr '\n' ' ')
if [[ -n "$left" ]]; then say "KILL to marked: $left"; kill -KILL $left 2>/dev/null; sleep 3; fi
# go.sh ends by itself when its pipeline ends; the stopped timeout cannot reap it, so it may stay a zombie
for i in 1 2 3 4 5; do [[ -n "$GO" && -d /proc/$GO && "$(awk '{print $3}' /proc/$GO/stat 2>/dev/null)" != Z ]] || break; sleep 2; done
if [[ -n "$GO" && -d /proc/$GO && "$(awk '{print $3}' /proc/$GO/stat 2>/dev/null)" != Z ]]; then kill -TERM "$GO" 2>/dev/null; sleep 2; fi
if [[ -n "$GO" && -d /proc/$GO && "$(awk '{print $3}' /proc/$GO/stat 2>/dev/null)" != Z ]]; then kill -KILL "$GO" 2>/dev/null; sleep 1; fi
# the timeout was stopped to move the walk's limit; continue it so that it reaps its child and exits
if [[ -n "$TO" && -d /proc/$TO ]]; then kill -CONT "$TO" 2>/dev/null; sleep 3; fi
if [[ -n "$TO" && -d /proc/$TO ]]; then kill -KILL "$TO" 2>/dev/null; sleep 1; fi
say "proof: marked left [$(marked | tr '\n' ' ')]; go.sh alive: $([[ -n "$GO" && -d /proc/$GO ]] && echo yes || echo no); timeout alive: $([[ -n "$TO" && -d /proc/$TO ]] && echo yes || echo no)"
ps -u "$me" -o pid=,ppid=,stat=,etime=,args= --width 200 | grep 'a15_f16' | grep -v -e grep -e 'n/stop.sh' -e 'n/wd.sh' -e ' ps -u' > "$LOG.ps"
say "proof: ps lines naming a15_f16 besides this stop and the watchdog: $(grep -c . "$LOG.ps")"
say "gpus: $(nvidia-smi --query-gpu=index,memory.used --format=csv,noheader 2>/dev/null | tr '\n' ';') apps [$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>/dev/null | tr '\n' ';')]"
