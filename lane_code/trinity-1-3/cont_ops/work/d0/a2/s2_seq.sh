#!/bin/bash
# Stage 2 (after stage 1 passed, same job and node): every rank's first batch through the full forward on CPU with the
# sealed code, one rank per process, inside the kit's own namespace and environment for mode p. Changes no kit file.
# Usage: s2.sh CAP_SECONDS. A rank call that the cap ends is killed; its rank is reported as not measured.
set -euo pipefail
CAP=${1:?}; T0=$(date +%s)
KH=/project/community/jjyeung/okh7/x_8417c021; IN=/project/community/jjyeung/okh7/i_bb09a77d
LOG=$KH/o/${SLURM_JOB_ID:?}.s2.steps
note() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
export TK_KIT_HOME=$KH TK_RUNS_DIR=/tmp/jjyeung/okit_8865619b/runs
source "$KH/b/c.sh"
export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID}.s2
mkdir -p "$TK_JOBDIR"
read -r rfile rsha < <(tk_current record)
[[ -f "$S/c7d31ddd/anyhost/$rsha.json" && -d "$NX/b" ]] || { note "stage 1 staging absent on this node"; exit 3; }
R1_RUNTIME_RECORD="$P/anyhost/$rsha.json"
tk_bwrap
tk_env
tk_pythonpath p
export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 CUDA_VISIBLE_DEVICES="" STUDENT_IO_THREADS=16
note "stage 2 start, cap $CAP s, mem $(free -g | awk 'NR==2 {print $2}') GiB"
rc=0
for n in 1 2 3 4; do
    left=$(( T0 + CAP - $(date +%s) ))
    (( left > 300 )) || { note "cap reached before rank call $n"; rc=124; break; }
    set +e
    timeout -s KILL "$left" "${BW[@]}" "$PILOT_VENV/bin/python" -B "$IN/a2/s2.py" "$X" > "$KH/o/${SLURM_JOB_ID}.s2.$n.log" 2>&1
    rc=$?
    set -e
    note "rank call $n rc=$rc"
    [[ $rc -eq 75 ]] || break
done
tk_persist_small
note "stage 2 end rc=$rc"
exit "$rc"
