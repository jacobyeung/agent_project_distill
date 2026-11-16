#!/usr/bin/env bash
# Detached Devin lane from the trusted repo root, no terminal. Run it ON the node that should host the lane.
# Usage: devin_bg.sh <lane> <brief> <model> <seconds>   (lane work dir: /scratch/jjyeung/orch_n30/<lane> on this node)
# Events and status mirrors: /data2/.../orch_n30/events/<lane>/
set -u
[[ $# -eq 4 ]] || { echo "usage: devin_bg.sh <lane> <brief> <model> <seconds>" >&2; exit 2; }
LANE=$1; BRIEF=$2; MODEL=$3; SECS=$4
[[ -f "$BRIEF" ]] || { echo "no brief $BRIEF" >&2; exit 2; }
W=/scratch/jjyeung/orch_n30/$LANE
mkdir -p "$W/out/devin_traces" "$W/work" "$W/inbox"
S=$(date -u +%Y%m%dT%H%M%SZ); OUT="$W/out/devin_$S.stdout"; EXP="$W/out/devin_traces/devin_$S.export.json"
cd /home/jjyeung/agent_project_distill || exit 3
setsid nohup timeout "$SECS" /home/jjyeung/.local/bin/devin -p --prompt-file "$BRIEF" --permission-mode dangerous --model "$MODEL" --export "$EXP" < /dev/null > "$OUT" 2>&1 &
P=$!
printf '{"utc":"%s","lane":"%s","brief":"%s","model":"%s","secs":%s,"pid":%s,"host":"%s"}\n' "$S" "$LANE" "$BRIEF" "$MODEL" "$SECS" "$P" "$(hostname -s)" >> "$W/out/devin_launches.jsonl"
echo "$(hostname -s) $P $OUT"
