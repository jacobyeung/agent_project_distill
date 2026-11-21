#!/bin/bash
# fix16 walk of the kit's mode q from the start of a.py, in scratch, under one spelling of the run root.
# usage: go.sh <run name> <NS|NJ> [candidate folder]   (inside srun --overlap --jobid 174198)
# Writes only under /tmp/a15_f16_174198. CPU only (no device visible in the sandbox).
set -uo pipefail
export TZ=UTC
umask 077
JOB=174198; D=/tmp/a15_f16_$JOB; N16=$D/n
NAME=${1:?}; SPELL=${2:-NS}; CAND=${3:-$N16/cand}
RUN=$D/$NAME; LOG=$RUN/log
[[ -e "$RUN" ]] && { echo "run folder exists: $RUN"; exit 2; }
mkdir -p "$LOG"; chmod 700 "$D" "$RUN"
say() { echo "$(date -u +%FT%TZ) $*" >> "$LOG/go.log"; }
say "start $NAME spelling $SPELL candidate $CAND on $(hostname -s) pid $$"
Q_ROOT=/tmp/q_22c714e1_$JOB; Q_NS=/tmp/q_22c714e1; Q_KIT=/project/community/jjyeung/okh7/x_22c714e1/n
TK_KIT_HOME=$Q_ROOT/h; TK_JOBDIR=$Q_ROOT/j; TK_JOB_START=$(date +%s); A16_LAYOUT=walk
export SLURM_JOB_ID=$JOB
source "$N16/L16.sh" > "$LOG/sandbox.out" 2>&1 || { say "sandbox setup failed: $(tail -c 300 "$LOG/sandbox.out")"; exit 3; }
# the incoming request, as z.bootstrap writes it from the resolve output
/usr/bin/python3 -B -I -c 'import sys; sys.path.insert(0,sys.argv[1]+"/b"); from z import load,write; write(sys.argv[3],dict(_resolved=load(sys.argv[2])))' "$Q_KIT" "$Q_ROOT/r0.json" "$W/top/r.json" || { say "request build failed"; exit 3; }
case "$SPELL" in NS) ROOTNS=$Q_NS ;; NJ) ROOTNS=$Q_NJ ;; *) say "bad spelling"; exit 2 ;; esac
printf '%s\n' "${BW[@]}" > "$LOG/bwrap_args.txt"
sha256sum "$CAND/b/a.py" "$CAND/b/pf.py" "$N16/ta.py" "$N16/L16.sh" "$Q_KIT/SHA256SUMS.txt" >> "$LOG/go.log"
say "a.py q $ROOTNS/p $ROOTNS/r.json"
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$N16/ta.py" "$CAND" "$Q_KIT" q "$ROOTNS/p" "$ROOTNS/r.json" 2> "$LOG/q.err" | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$LOG/q.log"
rc=${PIPESTATUS[0]}
echo "$rc" > "$LOG/rc"
say "a.py exit $rc"
