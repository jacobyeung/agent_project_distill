#!/usr/bin/env bash
# Health check, then start a lane on THIS node. Usage: launch_remote.sh <lane> <seconds> [min free GB on /scratch]
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
LANE=$1; SECS=$2; MINFREE=${3:-150}
H=$(hostname -s)
echo "host=$H $(date -u +%FT%TZ) load=$(cut -d' ' -f1-3 /proc/loadavg) cpus=$(nproc)"
[[ "$H" == trinity ]] && { echo "REFUSE head node"; exit 1; }
FREE=$(df -BG --output=avail /scratch | tail -1 | tr -dc 0-9)
echo "scratch_free_G=$FREE mem_G: $(free -g | awk 'NR==2{print $2" total "$7" avail"}')"
(( FREE >= MINFREE )) || { echo "REFUSE scratch below $MINFREE G"; exit 1; }
if pgrep -u jjyeung -f "prompt-file $B/briefs/$LANE.md" > /dev/null; then echo "REFUSE lane already running here"; exit 1; fi
[[ -x /home/jjyeung/.local/bin/devin ]] || { echo "REFUSE no devin"; exit 1; }
mkdir -p "$B/events/$LANE"
bash "$B/tools/devin_bg.sh" "$LANE" "$B/briefs/$LANE.md" claude-opus-5-5-high "$SECS"
sleep 25
for p in $(pgrep -u jjyeung -f "prompt-file $B/briefs/$LANE.md" | head -n 3); do ps -o pid=,stat=,etime=,comm= -p "$p"; done
head -c 300 /scratch/jjyeung/orch_n30/$LANE/out/devin_*.stdout 2>/dev/null
echo "launch_remote done"
