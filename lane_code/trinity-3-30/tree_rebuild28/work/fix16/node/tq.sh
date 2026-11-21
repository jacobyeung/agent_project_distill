#!/bin/bash
# fix16 quick read-only test of the candidate's frame-root naming on the refused run's staged bytes.
# usage: tq.sh <run name>   (inside srun --overlap --jobid 174198). Writes only under /tmp/a15_f16_174198.
set -uo pipefail
export TZ=UTC
umask 077
JOB=174198; D=/tmp/a15_f16_$JOB; N16=$D/n; NAME=${1:?}
RUN=$D/$NAME; LOG=$RUN/log
[[ -e "$RUN" ]] && { echo "run folder exists: $RUN"; exit 2; }
mkdir -p "$LOG"; chmod 700 "$D" "$RUN"
Q_ROOT=/tmp/q_22c714e1_$JOB; Q_NS=/tmp/q_22c714e1; Q_KIT=/project/community/jjyeung/okh7/x_22c714e1/n
TK_KIT_HOME=$Q_ROOT/h; TK_JOBDIR=$Q_ROOT/j; TK_JOB_START=$(date +%s); A16_LAYOUT=ro
export SLURM_JOB_ID=$JOB
source "$N16/L16.sh" > "$LOG/sandbox.out" 2>&1 || { echo "sandbox setup failed: $(tail -c 300 "$LOG/sandbox.out")"; exit 3; }
mkdir -p "$RUN/o"
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$N16/tq.py" "$Q_KIT" "$N16/cand" "$RUN/o" > "$LOG/tq.out" 2>&1
echo "rc=$?" >> "$LOG/tq.out"
cut -c1-1500 "$LOG/tq.out" | tail -n 60
