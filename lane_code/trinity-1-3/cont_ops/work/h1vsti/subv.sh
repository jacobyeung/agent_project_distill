#!/bin/bash
# gated submit of the step-544 R0-dev read (token ${TOK:?}); run from work/h1vsti
set -u; cd /scratch/jjyeung/orch_n30/cont_ops/work/h1vsti
export PYTHONDONTWRITEBYTECODE=1 PY=/scratch/jjyeung/envs/p1cpu/bin/python L=$PWD/kit/launcher/orchard_launcher.py
export A_TRANSPORT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
dest=$PWD/kit/build/${TOK:?}
test -s $dest/SUBMIT.out && { echo "REFUSED: already submitted"; cat $dest/SUBMIT.out; exit 8; }
G=$(timeout 120 bash $A_TRANSPORT 'TZ=UTC squeue -u jjyeung -p general -h -o "%i %j %T %r"' 2>&1); echo "GEN[$G]"
[ -n "$G" ] && { echo "REFUSED: general not clear"; exit 9; }
cmd=$("$PY" -B "$L" submit-command --destination "$dest") || exit 2
timeout 300 bash "$A_TRANSPORT" "$cmd" < "$dest/BATCH.sh" > "$dest/SUBMIT.out" 2> "$dest/SUBMIT.err"; echo "submit rc=$?"
cat $dest/SUBMIT.out; tail -3 $dest/SUBMIT.err
"$PY" -B "$L" record-submission --destination "$dest"; echo "record rc=$?"
