#!/bin/bash
# r1_ops9: ORDER 1010Z item 2 plan B trigger. From START (epoch) poll Orchard every 60 s; when 172660 has left the queue
# (sacct terminal) and m600/DONE.json is absent, submit plan B (pbjob 3aeb20ae on 6ed2c7aa 600) once, write ledger + BLOCKER.
W=/scratch/jjyeung/orch_n30/r1_ops6/work/r9; E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh; START=${1:?epoch}
while (( $(date +%s) < START )); do [[ -e $W/pbw.stop ]] && exit 0; sleep 30; done
fails=0
while :; do
  [[ -e $W/pbw.stop ]] && { echo "$(date -u +%T) stop file"; exit 0; }
  out=$(timeout 120 bash $OSSH 'bash -s' < $W/pbw_remote.sh 2>&1); rc=$?
  echo "$(date -u +%T) rc=$rc $(echo "$out" | tr '\n' ' ' | cut -c1-400)" | tee -a $W/pbw.hist > $W/pbw.last
  if (( rc != 0 )); then fails=$((fails+1)); (( fails >= 2 )) && { touch $W/pbw.alarm; }; sleep 60; continue; fi; fails=0
  if [[ $out == *DONE_PRESENT* ]]; then echo "$out" > $W/pbw.final; exit 0; fi
  if [[ $out == *SUBMITTED* ]]; then
    echo "$out" > $W/pbw.final; tok=$(echo "$out" | grep -o 'token=[0-9a-f]*' | cut -d= -f2); job=$(echo "$out" | grep -o 'job=[0-9]*' | head -1 | cut -d= -f2)
    printf '{"utc":"%s","token":"a15_cot_ap%s","job":"%s","run":"6ed2c7aa","step":600,"purpose":"pb600","meaning":"ORDER 1010Z item 2 plan B: 172660 left the queue without m600/DONE.json; recompute handover receipt (pbs_3aeb20ae.sh) out okh7/pb_%s","lane":"r1_ops9"}\n' "$(date -u +%FT%TZ)" "$tok" "$job" "$tok" >> /scratch/jjyeung/orch_n30/r1_ops6/work/ORCHARD_LEDGER.jsonl
    S=$(date -u +%Y%m%dT%H%MZ); f=$E/${S}_BLOCKER_r1_ops9_plan_b_running.md
    { echo "# BLOCKER r1_ops9 (ORDER 1010Z item 2): job 172660 left the queue without m600/DONE.json; plan B is running"
      echo "- Plan B job a15_cot_ap$tok = $job submitted $(date -u +%T)Z (preempt, pbjob 3aeb20ae on r/6ed2c7aa/A.tar + m600 export; out okh7/pb_$tok)."
      echo "- Rehearsal took 16.7 min after start (RESULT 1108Z), so ETA ~17 min after it starts; queue delay extra."
      echo "- Trigger output: $(echo "$out" | tr '\n' ' ' | cut -c1-600)"; } > $f
    exit 0
  fi
  [[ $out == *SCRIPT_SHA_DIFFERS* || $out == *OUT_EXISTS* ]] && { touch $W/pbw.alarm; exit 1; }
  sleep 60
done
