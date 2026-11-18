#!/bin/bash
# cont_ops6: submit one prepared D0 read (readk/REPORT.md path) with --time 01:45:00 (ORCH ruling 0940Z) and an on-Orchard general-empty guard.
# Usage: bash subread.sh TOKEN DEADLINE_UTC (e.g. 2026-11-16T17:40:00; ORCH ruling 1102Z: limit must end before 17:45Z)   (exit 9 = general busy, nothing submitted)
set -u
cd /scratch/jjyeung/orch_n30/cont_ops/work/d0/readk || exit 1
export PYTHONDONTWRITEBYTECODE=1
PY=/scratch/jjyeung/envs/p1cpu/bin/python L=$PWD/kit/launcher/orchard_launcher.py
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
DEST=$PWD/kit/build/$1
[ -e "$DEST/SUBMIT.out" ] && { echo "SUBMIT.out exists; never resubmit"; exit 1; }
CMD=$("$PY" -B "$L" submit-command --destination "$DEST") || exit 1
[ "$(grep -o -- '--time=06:00:00' <<<"$CMD" | wc -l)" = 2 ] || [ "$(grep -o -- '--time=06:00:00' <<<"$CMD" | wc -l)" = 1 ] || { echo "time flag count unexpected"; exit 1; }
DL=${2:?deadline}; now=$(date -u +%s); dl=$(date -u -d "${DL/T/ }" +%s) || exit 1
(( now + 6300 + 120 <= dl )) || { echo "now + 01:45 does not end before deadline $DL; not submitting"; exit 8; }
Q="'\"'\"'"; NEW="--time=01:45:00${Q}, ${Q}--deadline=$DL"; CMD2=${CMD//--time=06:00:00/$NEW}
FULL="export TZ=UTC; [ -z \"\$(squeue -h -u jjyeung -p general)\" ] || { echo GENERAL_BUSY >&2; squeue -h -u jjyeung -p general >&2; exit 9; }; $CMD2"
echo "$CMD2" > "$DEST/SUBMIT.cmd"
timeout 300 bash "$OSSH" "$FULL" < "$DEST/BATCH.sh" > "$DEST/SUBMIT.out.tmp" 2> "$DEST/SUBMIT.err"; rc=$?
echo "rc=$rc"; cat "$DEST/SUBMIT.err" | tail -5
if [ $rc = 9 ]; then mv "$DEST/SUBMIT.out.tmp" "$DEST/SUBMIT.busy.$(date -u +%H%M)"; exit 9; fi
mv "$DEST/SUBMIT.out.tmp" "$DEST/SUBMIT.out"; cat "$DEST/SUBMIT.out"
[ $rc = 0 ] && "$PY" -B "$L" record-submission --destination "$DEST"
exit $rc
