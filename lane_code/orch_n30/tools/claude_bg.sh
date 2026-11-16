#!/usr/bin/env bash
# Detached headless Claude Code lane on THIS node (run it on the node that should host the lane).
# Usage: claude_bg.sh <lane> <brief> <model> <effort> <seconds>
# Lane dir /scratch/jjyeung/orch_n30/<lane> (cwd, not a git tree); stream-json transcript in <lane>/out/.
set -u
[[ $# -eq 5 ]] || { echo "usage: claude_bg.sh <lane> <brief> <model> <effort> <seconds>" >&2; exit 2; }
LANE=$1; BRIEF=$2; MODEL=$3; EFFORT=$4; SECS=$5
[[ "$(hostname -s)" == trinity ]] && { echo "REFUSE head node" >&2; exit 1; }
[[ -f "$BRIEF" ]] || { echo "no brief $BRIEF" >&2; exit 2; }
W=/scratch/jjyeung/orch_n30/$LANE; mkdir -p "$W/out" "$W/work" "$W/inbox"
S=$(date -u +%Y%m%dT%H%M%SZ); OUT="$W/out/claude_$S.jsonl"
cd "$W" || exit 3
export XDG_CACHE_HOME=/scratch/jjyeung/.cache
setsid nohup timeout "$SECS" /home/jjyeung/.local/bin/claude -p "You are distillation lane $LANE on node $(hostname -s). Your brief is the file $BRIEF. Read it and do all the work it describes, following every rule file it names. Do not end your turn while work is owed; wait with sleep of at most 10 minutes between checks." --model "$MODEL" --effort "$EFFORT" --dangerously-skip-permissions --output-format stream-json --verbose < /dev/null > "$OUT" 2>&1 &
P=$!
printf '{"utc":"%s","lane":"%s","brief":"%s","model":"%s","effort":"%s","secs":%s,"pid":%s,"host":"%s"}\n' "$S" "$LANE" "$BRIEF" "$MODEL" "$EFFORT" "$SECS" "$P" "$(hostname -s)" >> "$W/out/claude_launches.jsonl"
echo "$(hostname -s) $P $OUT"
