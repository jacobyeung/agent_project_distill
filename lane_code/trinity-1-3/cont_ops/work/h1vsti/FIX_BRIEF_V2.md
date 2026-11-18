# Kit fork h1vsti, round V2: finish round V1's validation and reseal

Same scope and rules as FIX_BRIEF_V1.md (read it, then FIXV1.md, which you wrote). Work only inside `/scratch/jjyeung/orch_n30/cont_ops/work/h1vsti/`; h1read and the packets stay read-only.

AUTHORIZED: reading files on `/scratch` (node-local disk) is not heavy IO under the cluster rules; those rules restrict /home and /data* (NFS). Run the full suites REPORT.md lists, the real-RGB runtime fixtures, the legacy plan matrix (a7 and main prepares of every admitted run byte-identical to h1read fix 6), and reseal the fork (its own FINAL_PINS and SHA256SUMS). Do not read large files from /home or /data*.

Deliver by 11:05Z: append to FIXV1.md a "Validation" section listing each suite with pass/fail counts and log paths under evidence/, the new FINAL_PINS and SHA256SUMS sha256, and any failure with its cause. Change code only to fix a failure these runs expose, and list each such change with file:line. Also replace `PY=python3` in the operator commands with `/scratch/jjyeung/envs/p1cpu/bin/python` if the kit's prior rounds used that interpreter (FIX6.md), and use `A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh` as FIX6.md does unless tools/operator_transport.sh is strictly required (say why).
