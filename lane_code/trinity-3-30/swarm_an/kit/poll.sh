#!/bin/bash
# One compact poll for lane swarm_an: inboxes, orchestrator events, cont_ops events, running analysts. usage: poll.sh [seconds to sleep first]
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
W=/scratch/jjyeung/orch_n30
[ -n "$1" ] && sleep "$1"
echo "== $(date -u +%H:%MZ)"
for d in $W/swarm_an/inbox $W/swarm_an4/inbox; do n=$(ls $d | wc -l); [ "$n" -gt 0 ] && { echo "inbox $d:"; ls -t $d | head -5; }; done
echo "swarm_an events (newest 3):"; ls -t $B/events/swarm_an | grep -v -E "STATUS.md|\.tar$|^prompts$" | head -3
echo "cont_ops events (newest 4):"; ls -t $B/events/cont_ops | grep -v -E "^STATUS.md$|^files" | head -4
for l in $W/san_dd_vsticam; do
  [ -d $l ] || continue
  if [ -f $l/DONE ]; then echo "$(basename $l): DONE"; else echo "$(basename $l): running=$(pgrep -f "prompts/none|briefs/$(basename $l).md" | wc -l) $(head -c 300 $l/STATUS.md 2>/dev/null | tr '\n' ' ')"; fi
done
tmux ls 2>/dev/null | grep -E "san_q" | cut -c1-60
