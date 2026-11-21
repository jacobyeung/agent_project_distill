#!/bin/bash
# Node layout pre-check (CPU only, no GPU, nothing of the job written): builds the rehearsal sandbox on the
# job's current folder and runs pre.py in it; then shows that the probes exist only in scratch.
set -uo pipefail; export TZ=UTC; umask 077
JOB=${A15_JOB:-174198}; D=${A15_D:-/tmp/a15_rh_$JOB}; RH=$D/rh
RUN=$D/pre_$(date -u +%Y%m%dT%H%M%SZ); mkdir -p "$RUN/log"
JSH=$(pgrep -u "$(id -u)" -f "^/bin/bash /tmp/q_22c714e1_$JOB/j.sh$" | head -1)
envof() { [[ -n "$JSH" ]] && tr '\0' '\n' < "/proc/$JSH/environ" 2>/dev/null | sed -n "s/^$1=//p" | head -1; }
Q_ROOT=$(envof Q_ROOT); Q_ROOT=${Q_ROOT:-/tmp/q_22c714e1_$JOB}; Q_NS=$(envof Q_NS); Q_NS=${Q_NS:-/tmp/q_22c714e1}
Q_KIT=$(envof Q_KIT); Q_KIT=${Q_KIT:-/project/community/jjyeung/okh7/x_22c714e1/n}
TK_KIT_HOME=$(envof TK_KIT_HOME); TK_KIT_HOME=${TK_KIT_HOME:-$Q_ROOT/h}; TK_JOBDIR=$(envof TK_JOBDIR); TK_JOBDIR=${TK_JOBDIR:-$Q_ROOT/j}
TK_JOB_START=$(envof TK_JOB_START); TK_JOB_START=${TK_JOB_START:-0}
echo "j.sh pid ${JSH:-none}: Q_ROOT=$Q_ROOT Q_NS=$Q_NS Q_KIT=$Q_KIT TK_KIT_HOME=$TK_KIT_HOME TK_JOBDIR=$TK_JOBDIR TK_JOB_START=$TK_JOB_START ($(date -u -d @$TK_JOB_START +%TZ))"
export JOB RUN RH Q_ROOT Q_NS Q_KIT TK_KIT_HOME TK_JOBDIR TK_JOB_START
source "$RH/L.sh" || { echo "sandbox build failed"; exit 3; }
printf '%s\n' "${BW[@]}" > "$RUN/log/bwrap_args.txt"; echo "sandbox args: ${#BW[@]}"
"${BW[@]}" nice -n 10 "$PILOT_VENV/bin/python" -B -s "$RH/pre.py" "$RUN/seal_copy.json" 2>&1 | tail -c 4000; echo "pre rc=${PIPESTATUS[0]}"
echo "host side: job folder has a15probe/a15new/a15x files: [$(ls "$Q_ROOT"/a15probe "$Q_ROOT"/p/a15probe "$Q_ROOT"/p/a15new "$Q_ROOT"/p/q/r/a15probe "$Q_ROOT"/p/q/f/a15x "$Q_ROOT"/j/tmp/a15probe "$Q_ROOT"/cache/a15probe "$Q_ROOT"/t.log 2>/dev/null | tr '\n' ' ')]"
echo "scratch side: $(cd "$RUN/w" && find . -name 'a15*' | tr '\n' ' ')"
