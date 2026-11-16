#!/bin/bash
# Stage 2 (after stage 1 passed, same job and node): every rank's first batch through the full forward on CPU with the
# sealed code, one process per rank (four at once with 64 cores, else two at a time), 16 threads each, inside the kit's own
# namespace and environment for mode p. Changes no kit file. Usage: s2.sh CAP_SECONDS.
# A rank process the cap ends is killed; its rank is reported as not measured.
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
cores=$(nproc); par=4; (( cores >= 64 )) || par=2
note "stage 2 start, cap $CAP s, $cores cores, $par rank processes at a time, mem $(free -g | awk 'NR==2 {print $2}') GiB"
declare -A rc
run_rank() {  # rank, seconds left
    timeout -s KILL "$2" "${BW[@]}" "$PILOT_VENV/bin/python" -B "$IN/a2/s2.py" "$X" "$1" 512 > "$KH/o/${SLURM_JOB_ID}.s2.r$1.log" 2>&1
}
groups=("0 1 2 3"); (( par == 4 )) || groups=("0 1" "2 3")
for g in "${groups[@]}"; do
    left=$(( T0 + CAP - $(date +%s) ))
    if (( left <= 600 )); then for r in $g; do rc[$r]=124; note "rank $r not started: cap reached"; done; continue; fi
    declare -A pid=()
    for r in $g; do run_rank "$r" "$left" & pid[$r]=$!; done
    for r in $g; do set +e; wait "${pid[$r]}"; rc[$r]=$?; set -e; note "rank $r rc=${rc[$r]}"; done
done
all=0; for r in 0 1 2 3; do [[ "${rc[$r]:-1}" == 0 ]] || all=1; done
if (( all == 0 )); then
    left=$(( T0 + CAP + 900 - $(date +%s) ))
    set +e; timeout -s KILL "$left" "${BW[@]}" "$PILOT_VENV/bin/python" -B "$IN/a2/s2.py" "$X" final 512 > "$KH/o/${SLURM_JOB_ID}.s2.final.log" 2>&1; frc=$?; set -e
    note "admission receipt call rc=$frc"
else
    frc=9; note "admission receipt call not made: not every rank passed"
fi
tk_persist_small
note "stage 2 end"
exit "$frc"
