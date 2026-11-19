#!/bin/bash
# On trinity-2-28: start a Cursor Opus review for each Codex build when its codex.log shows EXIT=.
I=/scratch/jjyeung/orch_n30/sm_ship2
for i in $(seq 1 240); do
  left=0
  for t in filter move; do
    N=sm_cr_$t; W=/scratch/jjyeung/orch_n30/$N
    tmux has-session -t "=$N" 2>/dev/null && continue
    [ -f $W/cursor.log ] && continue
    if grep -q '^EXIT=' /scratch/jjyeung/orch_n30/sm_$t/codex.log 2>/dev/null; then
      mkdir -p $W; cp $I/CURSOR_AGENTS.md $W/AGENTS.md; cp $I/cr_$t.md $W/PROMPT.md
      tmux new-session -d -s $N "cd $W && export XDG_CACHE_HOME=/scratch/jjyeung/.cache; nice -n 10 timeout 5400 /home/jjyeung/.local/bin/agent -p -f --sandbox disabled --trust --model claude-opus-5-5-xhigh \"\$(cat $W/PROMPT.md)\" > $W/cursor.log 2>&1; echo EXIT=\$? >> $W/cursor.log"
      echo "$(date -u +%FT%TZ) started $N"
    else left=1; fi
  done
  [ $left = 0 ] && { echo "$(date -u +%FT%TZ) all started"; exit 0; }
  sleep 30
done
