#!/bin/bash
# cursor_start.sh <name> <prompt file> : read-only Cursor Opus review in /scratch/jjyeung/orch_n30/<name> on this node
set -u
N=$1; PR=$2; W=/scratch/jjyeung/orch_n30/$N; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
mkdir -p $W; cp $P/CURSOR_AGENTS.md $W/AGENTS.md; cp $PR $W/PROMPT.md
tmux has-session -t "=$N" 2>/dev/null && { echo "$N exists"; exit 0; }
tmux new-session -d -s $N "cd $W && export XDG_CACHE_HOME=/scratch/jjyeung/.cache; nice -n 10 timeout 5400 /home/jjyeung/.local/bin/agent -p -f --sandbox disabled --trust --model claude-opus-5-5-xhigh \"\$(cat $W/PROMPT.md)\" > $W/cursor.log 2>&1; echo EXIT=\$? >> $W/cursor.log"
echo "started cursor $N"
