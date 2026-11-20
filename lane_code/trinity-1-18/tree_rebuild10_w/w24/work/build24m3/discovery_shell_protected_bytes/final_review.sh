set -euo pipefail
Q_KIT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/discovery_shell_protected_bytes/kit
Q_ROOT=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/discovery_shell_protected_bytes/nodes/q_22c714e1_94
Q_NS=/tmp/q_22c714e1
PILOT_VENV=/scratch/jjyeung/envs/p1cpu
BW=(/usr/bin/bwrap --ro-bind / / --dev-bind /dev /dev --proc /proc --tmpfs /tmp --bind /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/discovery_shell_protected_bytes/nodes/q_22c714e1_94 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/discovery_shell_protected_bytes/nodes/q_22c714e1_94 --bind /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/discovery_shell_protected_bytes/nodes/q_22c714e1_94 /tmp/q_22c714e1 --bind /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/discovery_shell_protected_bytes/target /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m3/discovery_shell_protected_bytes/target)

"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/h.py" "$Q_NS/p" "$Q_NS/v.json"
"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/rv.py" "$Q_NS" "$Q_NS/v.json" "$SLURM_JOB_ID"
