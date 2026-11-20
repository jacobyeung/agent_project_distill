set -euo pipefail
Q_KIT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/build24m4c/discovery_shell_protected_bytes/kit
Q_ROOT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/build24m4c/discovery_shell_protected_bytes/nodes/q_22c714e1_94
Q_NS=/tmp/q_22c714e1
PILOT_VENV=/scratch/jjyeung/envs/p1cpu
BW=(/usr/bin/bwrap --ro-bind / / --dev-bind /dev /dev --proc /proc --tmpfs /tmp --bind /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/build24m4c/discovery_shell_protected_bytes/nodes/q_22c714e1_94 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/build24m4c/discovery_shell_protected_bytes/nodes/q_22c714e1_94 --bind /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/build24m4c/discovery_shell_protected_bytes/nodes/q_22c714e1_94 /tmp/q_22c714e1 --bind /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/build24m4c/discovery_shell_protected_bytes/target /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/build24m4c/discovery_shell_protected_bytes/target)
# Both invocations use the same logical namespace and separate physical roots.
mkdir -p "$Q_ROOT/dr"
cp "$Q_ROOT/r.json" "$Q_ROOT/dr/r.json"
set +e
"${BW[@]}" --bind "$Q_ROOT/dr" "$Q_NS" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/a.py" r "$Q_NS/p" "$Q_NS/r.json" 2>&1 | /scratch/jjyeung/envs/p1cpu/bin/python -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/dr/q.log"
rc=${PIPESTATUS[0]}
if [[ "$rc" != 0 ]]; then exit "$rc"; fi
cp "$Q_ROOT/dr/p/routing_selection.json" "$Q_ROOT/routing_selection.json"
/scratch/jjyeung/envs/p1cpu/bin/python -B -I -s "$Q_KIT/b/ep.py" "$Q_KIT" "$Q_ROOT" "${SLURM_JOB_ID:?}" 0
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/g.py"
rc=$?
if [[ "$rc" != 0 ]]; then exit "$rc"; fi
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/a.py" q "$Q_NS/p" "$Q_NS/r.json" 2>&1 | /scratch/jjyeung/envs/p1cpu/bin/python -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/q.log"
rc=${PIPESTATUS[0]}
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/d.py" "$Q_NS/p/s" "$Q_NS/r.json" "$Q_NS/n.json" "$Q_NS/rooms.json" 2>&1 | /scratch/jjyeung/envs/p1cpu/bin/python -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/rooms.log"
rr=${PIPESTATUS[0]}
if [[ "$rc" == 0 && "$rr" == 0 ]]; then
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/h.py" "$Q_NS/p" "$Q_NS/v.json" 2>&1 | /scratch/jjyeung/envs/p1cpu/bin/python -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/h.log"
rc=${PIPESTATUS[0]}
if [[ "$rc" == 0 ]]; then
"${BW[@]}" nice -n 10 "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/rv.py" "$Q_NS" "$Q_NS/v.json" "${SLURM_JOB_ID:?}" 2>&1 | /scratch/jjyeung/envs/p1cpu/bin/python -B "$Q_KIT/b/l.py" "$Q_KIT" > "$Q_ROOT/rv.log"
rc=${PIPESTATUS[0]}
fi
fi
/scratch/jjyeung/envs/p1cpu/bin/python -B "$Q_KIT/b/o.py" "$Q_ROOT" "$rc" "$rr"
exit "$rc"
