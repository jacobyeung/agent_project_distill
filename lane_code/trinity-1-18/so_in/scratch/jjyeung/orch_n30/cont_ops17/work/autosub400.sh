#!/bin/bash
# cont_ops17 step-400 auto-submit for a fix-7 kit: K=<h1read7|h1face7|h1vsti7> TOK=<token> STEP=400 LABEL=<direct|facing|vsti> [POLL=180]
# waits for x_ee227714/o/gcs_6ed2c7aa_m$STEP.done and general without RUNNING/non-held PENDING job of mine, submits once, then 1-min monitor with yield (mon16 logic)
set -u; W=/scratch/jjyeung/orch_n30/cont_ops/work; cd $W/${K:?}
export PYTHONDONTWRITEBYTECODE=1 PY=/scratch/jjyeung/envs/p1cpu/bin/python L=$PWD/kit/launcher/orchard_launcher.py
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh; export A_TRANSPORT=$O
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops
D=/project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m${STEP:?}.done; dest=$PWD/kit/build/${TOK:?}; LOG=$PWD/autosub400_$TOK.log; fails=0
test -s $dest/BATCH.sh || { echo "no package $dest" >> $LOG; exit 2; }
test -s $dest/SUBMIT.out && { echo "already submitted" >> $LOG; exit 8; }
for i in $(seq 1 600); do
  R=$(timeout 120 bash $O "test -s $D && echo DONE_OK; TZ=UTC squeue -u jjyeung -p general -h -o 'GEN %i %j %T %r'" 2>&1); rc=$?
  echo "$(date -u +%TZ) rc=$rc $(echo "$R" | tr '\n' '|')" >> $LOG
  if [ $rc -ne 0 ] && ! echo "$R" | grep -q 'GEN\|DONE_OK'; then fails=$((fails+1)); [ $fails -ge 3 ] && { S=$(date -u +%Y%m%dT%H%MZ); echo "# BLOCKER cont_ops17 autosub400 $LABEL: 3 failed ossh polls; see $LOG" > $E/${S}_BLOCKER_autosub400_${LABEL}_ossh.md; exit 4; }; sleep ${POLL:-180}; continue; fi
  fails=0
  BUSY=$(echo "$R" | awk '$1=="GEN" && ($4=="RUNNING" || $4=="CONFIGURING" || $4=="COMPLETING" || ($4=="PENDING" && $5 !~ /Held/))')
  if echo "$R" | grep -q DONE_OK && [ -z "$BUSY" ]; then
    cmd=$("$PY" -B "$L" submit-command --destination "$dest") || { echo "submit-command failed" >> $LOG; exit 2; }
    timeout 300 bash $O "$cmd" < "$dest/BATCH.sh" > "$dest/SUBMIT.out" 2> "$dest/SUBMIT.err"; echo "submit rc=$?" >> $LOG
    "$PY" -B "$L" record-submission --destination "$dest" >> $LOG 2>&1
    J=$(head -1 $dest/SUBMIT.out 2>/dev/null | grep -oE '^[0-9]+$'); S=$(date -u +%Y%m%dT%H%MZ)
    if [ -z "$J" ]; then printf '# BLOCKER cont_ops17 autosub400: %s m%s submit gave no job id (token %s); see %s and %s/SUBMIT.err\n' $LABEL $STEP $TOK $LOG $dest > $E/${S}_BLOCKER_${LABEL}_m${STEP}_submit.md; exit 5; fi
    printf '{"utc": "%s", "token": "a15_cot_ap%s", "meaning": "R1 C run 6ed2c7aa step %s %s read (%s fix 7), general 1 GPU; Orchard job %s", "lane": "cont_ops17"}\n' "$(date -u +%FT%TZ)" $TOK $STEP $LABEL $K $J >> $W/ORCHARD_LEDGER.jsonl
    printf '# RESULT cont_ops17: R1 C-prime m%s %s read submitted, Orchard %s (a15_cot_ap%s), general\n- Export .done present; general had no running job of mine. Kit %s (fix 7). 1-min monitor tmux mon400_%s (yields to jjy_*).\n' $STEP $LABEL $J $TOK $K $TOK > $E/${S}_RESULT_m${STEP}_${LABEL}_submitted_$J.md
    tmux new -d -s mon400_$TOK "J=$J TOK=$TOK K=$K bash /scratch/jjyeung/orch_n30/cont_ops17/work/mon400.sh"
    exit 0
  fi
  sleep ${POLL:-180}
done
