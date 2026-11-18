#!/bin/bash
# Stage 2 (after stage 1 passed and was published, same job and node): every rank's first batch through the full forward on
# CPU with the sealed code, one process per rank (four at once with 64 cores, else two at a time), 16 threads each, inside the
# kit's own namespace and environment for mode p. Changes no kit file. Usage: s2.sh CAP_SECONDS.
# Everything in this stage ends by CAP: rank processes by CAP - 900 s, the admission receipt call by CAP, the copy of its
# small records to project within 360 s after. A rank process the deadline ends is killed and reported as not measured.
set -euo pipefail
CAP=${1:?}; T0=$(date +%s); END=$(( T0 + CAP ))
KH=/project/community/jjyeung/okh7/x_8417c021; BUN=/project/community/jjyeung/okh7/i_bb09a77d/a3
LOG=$KH/o/${SLURM_JOB_ID:?}.s2.steps
note() { printf '%s | %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG" 2>/dev/null || true; }
export TK_KIT_HOME=$KH TK_RUNS_DIR=/tmp/jjyeung/okit_8865619b/runs
source "$KH/b/c.sh"   # assigns its own IN, R, P, S, U, X, NX, NR; this script uses BUN for its bundle
export TK_JOBDIR=/tmp/jjyeung/okit_$K/jobs/${SLURM_JOB_ID}.s2
mkdir -p "$TK_JOBDIR"
read -r rfile rsha < <(tk_current record)
[[ -f "$S/c7d31ddd/anyhost/$rsha.json" && -d "$NX/b" && -f "$BUN/s2.py" ]] || { note "stage 1 staging or bundle absent on this node"; exit 3; }
R1_RUNTIME_RECORD="$P/anyhost/$rsha.json"
tk_bwrap
tk_env
tk_pythonpath p
export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 CUDA_VISIBLE_DEVICES="" STUDENT_IO_THREADS=16
cores=$(nproc); par=4; (( cores >= 64 )) || par=2
note "stage 2 start, cap $CAP s, $cores cores, $par rank processes at a time, mem $(free -g | awk 'NR==2 {print $2}') GiB"
declare -A rc
run_rank() {  # rank, seconds left
    timeout -s KILL "$2" "${BW[@]}" "$PILOT_VENV/bin/python" -B "$BUN/s2.py" "$X" "$1" 512 > "$KH/o/${SLURM_JOB_ID}.s2.r$1.log" 2>&1
}
groups=("0 1 2 3"); (( par == 4 )) || groups=("0 1" "2 3")
for g in "${groups[@]}"; do
    left=$(( END - 900 - $(date +%s) ))
    if (( left <= 600 )); then for r in $g; do rc[$r]=124; note "rank $r not started: deadline reached"; done; continue; fi
    declare -A pid=()
    for r in $g; do run_rank "$r" "$left" & pid[$r]=$!; done
    for r in $g; do set +e; wait "${pid[$r]}"; rc[$r]=$?; set -e; note "rank $r rc=${rc[$r]}"; done
done
all=0; for r in 0 1 2 3; do [[ "${rc[$r]:-1}" == 0 ]] || all=1; done
frc=9
left=$(( END - $(date +%s) ))
if (( all == 0 && left > 60 )); then
    set +e; timeout -s KILL "$left" "${BW[@]}" "$PILOT_VENV/bin/python" -B "$BUN/s2.py" "$X" final 512 > "$KH/o/${SLURM_JOB_ID}.s2.final.log" 2>&1; frc=$?; set -e
    note "admission receipt call rc=$frc"
else
    note "admission receipt call not made: not every rank passed, or no time left"
fi
# The small-record copy of c.sh tk_persist_small, each rsync killed at its deadline (no descendant outlives it).
prc=0
timeout -s KILL 120 rsync -rt "$NX/o/" "$HM/o/" 2>/dev/null || prc=1
timeout -s KILL 120 rsync -rt "$NX/arm/" "$HM/arm/" 2>/dev/null || prc=1
timeout -s KILL 120 rsync -rt --prune-empty-dirs --exclude 'checkpoint_*' --exclude 'full_weights/' --exclude '*.pt' \
    --include '*/' --include '*.json' --include '*.jsonl' --exclude '*' "$NR/" "$HM/runs/" 2>/dev/null || prc=1
note "stage 2 records copied to project (failures $prc); stage 2 end"
exit "$frc"
