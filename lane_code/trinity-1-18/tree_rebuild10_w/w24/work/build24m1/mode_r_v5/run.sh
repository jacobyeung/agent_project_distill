set -uo pipefail
BW=(/usr/bin/bwrap --ro-bind / / --dev-bind /dev /dev --proc /proc --tmpfs /tmp --bind /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m1/mode_r_v5/node /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m1/mode_r_v5/node --bind /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m1/mode_r_v5/node /tmp/q_22c714e1 --bind /project/n/o/94/live /project/n/o/94/live --chdir /tmp/q_22c714e1)
PILOT_VENV=/scratch/jjyeung/envs/p1cpu
Q_KIT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m1/mode_r_v5/kit
Q_ROOT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m1/mode_r_v5/node
Q_NS=/tmp/q_22c714e1
export Q_MODE=r SLURM_JOB_ID=94
set +e
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m1/mode_r_v5/boundary.py "$Q_KIT/b/a.py" "${Q_MODE:-q}" "$Q_NS/p" "$Q_NS/r.json" 2>&1 | /scratch/jjyeung/envs/p1cpu/bin/python -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/q.log"
rc=${PIPESTATUS[0]}
if [[ "${Q_MODE:-q}" == r ]]; then
    /scratch/jjyeung/envs/p1cpu/bin/python -B -I -s "$Q_KIT/b/rd.py" "$Q_ROOT" "${SLURM_JOB_ID:?}" "$rc"
    rp=$?
    if [[ "$rc" == 0 ]]; then rc=$rp; fi
    exit "$rc"
fi
