set -uo pipefail
BW=()
PILOT_VENV=/scratch/jjyeung/envs/p1cpu
Q_KIT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m1/review_tests/go_identity/kit
Q_ROOT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m1/review_tests/go_identity/node/q_22c714e1_91
Q_NS="$Q_ROOT"
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/h.py" "$Q_NS/p" "$Q_NS/v.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/h.log"
rc=${PIPESTATUS[0]}
if [[ "$rc" == 0 ]]; then
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
"${BW[@]}" nice -n 10 "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/rv.py" "$Q_NS" "$Q_NS/v.json" "${SLURM_JOB_ID:?}" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/rv.log"
rc=${PIPESTATUS[0]}
fi
if [[ "$rc" == 0 ]]; then
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/t.py" "$Q_NS/p" "$Q_NS/v.json" 2>&1 | /usr/bin/python3 -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/t.log"
rc=${PIPESTATUS[0]}
fi

exit "$rc"
