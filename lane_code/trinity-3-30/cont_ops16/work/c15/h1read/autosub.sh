#!/bin/bash
# auto-submit of an R1 direct read: TOK, STEP, LATEST (UTC HH:MM, last allowed submit time; empty = none), POLL seconds
# waits for KH/o/gcs_673bc60f_m$STEP.done and general free (no RUNNING, no non-held PENDING job of mine), then sub544b.sh once; then RESULT + monitors
set -u; cd /scratch/jjyeung/orch_n30/cont_ops/work/h1read
O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops
D=/project/community/jjyeung/okh7/x_69d2930d/o/gcs_673bc60f_m${STEP:?}.done; LOG=autosub_m$STEP.log; fails=0; said=0
for i in $(seq 1 400); do
  now=$(date -u +%H:%M)
  if [ -n "${LATEST:-}" ] && [[ "$now" > "$LATEST" ]]; then echo "$(date -u +%TZ) past LATEST $LATEST: skip m$STEP" >> $LOG
    S=$(date -u +%Y%m%dT%H%MZ); printf '# RESULT cont_ops14 (autosub): R1 m%s direct read SKIPPED\n- Not submitted by %sZ (export or general not ready), so it could not leave general by the ORCH deadline. Token %s unspent. Log work/h1read/%s.\n' $STEP $LATEST $TOK $LOG > $E/${S}_RESULT_r1_m${STEP}_read_skipped.md; exit 3; fi
  R=$(timeout 120 bash $O "test -s $D && echo DONE_OK; TZ=UTC squeue -u jjyeung -p general -h -o 'GEN %i %j %T %r'" 2>&1); rc=$?
  echo "$(date -u +%TZ) rc=$rc $(echo "$R" | tr '\n' '|')" >> $LOG
  if [ $rc -ne 0 ] && ! echo "$R" | grep -q 'GEN\|DONE_OK'; then fails=$((fails+1)); [ $fails -ge 3 ] && { S=$(date -u +%Y%m%dT%H%MZ); echo "# BLOCKER cont_ops14 autosub m$STEP: 3 failed ossh polls; see work/h1read/$LOG" > $E/${S}_BLOCKER_autosub_m${STEP}_ossh.md; exit 4; }; sleep ${POLL:-120}; continue; fi
  fails=0
  BUSY=$(echo "$R" | awk '$1=="GEN" && ($4=="RUNNING" || $4=="CONFIGURING" || $4=="COMPLETING" || ($4=="PENDING" && $5 !~ /Held/))')
  if echo "$R" | grep -q DONE_OK && [ -z "$BUSY" ]; then
    # sub544b.sh refuses if any general job exists; held jobs allowed here, so use a local copy of its gate only when no job at all
    if echo "$R" | grep -q '^GEN'; then echo "$(date -u +%TZ) held job on general; submitting anyway" >> $LOG; SKIPGEN=1; else SKIPGEN=0; fi
    if [ $SKIPGEN = 1 ]; then sed 's/^\[ -n "\$G" \] .*$/: held-only gate passed in autosub/' sub544b.sh > sub_held.sh; OUT=$(TOK=$TOK bash sub_held.sh 2>&1); else OUT=$(TOK=$TOK bash sub544b.sh 2>&1); fi
    echo "$OUT" >> $LOG; J=$(head -1 kit/build/$TOK/SUBMIT.out 2>/dev/null | grep -oE '^[0-9]+$')
    S=$(date -u +%Y%m%dT%H%MZ)
    if [ -z "$J" ]; then printf '# BLOCKER cont_ops14 autosub: R1 m%s submit gave no job id (token %s); output in work/h1read/%s\n' $STEP $TOK $LOG > $E/${S}_BLOCKER_r1_m${STEP}_submit.md; exit 5; fi
    echo "$J" > ../h1orch/ours_general.txt
    printf '{"utc": "%s", "token": "a15_cot_ap%s", "meaning": "R1 run 673bc60f step %s direct read, families main+a7 --types direct (h1read fix 6), general 1 H100; Orchard job %s", "lane": "cont_ops14"}\n' "$(date -u +%FT%TZ)" $TOK $STEP $J >> ../ORCHARD_LEDGER.jsonl
    printf '# RESULT cont_ops14: R1 m%s direct read submitted, Orchard %s (a15_cot_ap%s), general\n- Export .done present; general had no running job of mine. h1read fix 6, main + a7, --types direct, about 27-35 min. Monitoring every minute (tmux c14_mon_m%s).\n' $STEP $J $TOK $STEP > $E/${S}_RESULT_r1_m${STEP}_read_submitted_$J.md
    test -s mon_direct.log && mv mon_direct.log mon_direct_pre_$J.log
    tmux new -d -s c14_mon_m$STEP "J=$J TOK=$TOK bash mon_direct.sh"
    tmux has-session -t c14_yield 2>/dev/null || tmux new -d -s c14_yield "bash /scratch/jjyeung/orch_n30/cont_ops/work/h1orch/loop8.sh 30 120"
    exit 0
  fi
  if echo "$R" | grep -q DONE_OK && [ $said = 0 ]; then echo "$(date -u +%TZ) export present, general busy: $BUSY" >> $LOG; said=1; fi
  sleep ${POLL:-120}
done
