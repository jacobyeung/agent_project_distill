#!/bin/bash
# Class tables for one D0 milestone read return (extracted on this node).
# Usage: run_milestone.sh STEP RETURN_ROOT [REVSI_JOURNAL]
#   RETURN_ROOT holds away/ and forward/ (each with a0/results/budget_2048/0/items_*.jsonl) and ITEMS.jsonl.
#   REVSI_JOURNAL (optional): B2048 journal of a ReVSI read of the same export.
set -euo pipefail
STEP=$1; R=$2; RV=${3:-}
LANE=/scratch/jjyeung/orch_n30/b13_facing; PY=/scratch/jjyeung/envs/p1cpu/bin/python
pick() { local f; f=$(ls "$R"/$1/a0/results/budget_2048/0/items_*.jsonl 2>/dev/null | head -1)
  [ -n "$f" ] || f=$(ls "$R"/$1/results/budget_2048/0/items_*.jsonl 2>/dev/null | head -1)
  [ -n "$f" ] || { echo "no B2048 journal for $1 under $R" >&2; exit 3; }
  "$PY" -I -c "import json,sys;b={json.loads(l).get('budget') for l in open(sys.argv[1]) if l.strip()};assert b<={2048},b" "$f"; echo "$f"; }
A=$(pick away); T=$(pick forward); IT=""; [ -f "$R/ITEMS.jsonl" ] && IT="--items $R/ITEMS.jsonl"
OUTROOT=${OUTROOT:-$LANE/out}; O=$OUTROOT/m$STEP; mkdir -p "$O"
"$PY" -I "$LANE/code/classify_away.py" --away "$A" --toward "$T" $IT --label "dev twins D0 step $STEP (B2048)" --out "$O/dev$STEP"
[ -n "$RV" ] && "$PY" -I "$LANE/code/classify_away.py" --away "$RV" --filter-type backward --label "ReVSI backward D0 step $STEP (B2048)" --out "$O/revsi$STEP"
sha256sum "$A" "$T" ${IT:+$R/ITEMS.jsonl} > "$O/INPUTS.sha256"
OUTROOT="$OUTROOT" "$PY" -I "$LANE/code/trend.py" > "$OUTROOT/TREND.md"
cat "$O"/*.md
