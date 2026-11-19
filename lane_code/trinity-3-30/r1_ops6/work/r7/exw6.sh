#!/bin/bash
# r1_ops8 copy for m600 (exw.sh stays untouched while r7m400 runs it): poll ${POLL:-120} s, rc-5 retry ${RETRY:-300} s.
# r1_ops7: export watcher for run 6ed2c7aa step $1, polling from $2 (epoch s): every 120 s one ossh call (exq.sh);
# on the upload marker: RESULT to events/cont_ops (ORDER 0014Z + ORDER 0054Z paths), then hr2.sh $1 (retry on rc 5
# every 300 s, at most 24 times), outputs in work/r7/m$1/, a factual RESULT to events/r1_ops. Stop file work/r7/m$1/stop.
S=$1; START=$2; W=/scratch/jjyeung/orch_n30/r1_ops6/work/r7; O=$W/m$S; mkdir -p $O
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
EV=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
flt() { grep -v -E "^@|WARNING: REMOTE|POSSIBLE|eavesdropping|host key|fingerprint|SHA256:lXw|contact your|google_compute_known|Offending|authentication is disabled"; }
while (( $(date +%s) < START )) && [[ ! -e $O/stop ]]; do sleep 60; done
while [[ ! -e $O/stop ]]; do
  timeout 300 bash $OSSH "bash -s $S" < $W/exq.sh 2>&1 | flt > $O/exq.tmp; mv $O/exq.tmp $O/exq.last; cat $O/exq.last >> $O/exq.hist
  grep -q "^DONE " $O/exq.last && break
  grep -q "^JOB " $O/exq.last || { tail -3 $O/exq.hist | grep -q "^JOB " || echo "job not in squeue $(date -u +%T)" >> $O/alarm; }
  sleep ${POLL:-120}
done
[[ -e $O/stop ]] && exit 0
read -r _ OBJ BYTES TARSHA < <(grep "^DONE " $O/exq.last); read -r _ DSHA DMT < <(grep "^DONESHA " $O/exq.last)
ART=$(grep "^ART " $O/exq.last | cut -d' ' -f2-)
T=$(date -u +%Y%m%dT%H%MZ)
cat > $EV/cont_ops/${T}_RESULT_from_r1_ops_Cprime_m${S}_export.md <<EOT
# RESULT r1_ops (auto, exw.sh) -> cont_ops (ORDER 0014Z): C' (job 172660, run 6ed2c7aa) step-$S export uploaded
- Step $S; export object $OBJ ($BYTES B, tar sha256 $TARSHA; bucket cmu-gpucloud-jjyeung, 4 parts).
- Receipt: /project/community/jjyeung/okh7/x_ee227714/o/gcs_6ed2c7aa_m$S.done sha256 $DSHA (written $(date -u -d @$DMT +%FT%TZ)).
- Artifact: /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/m$S/artifact.json sha256/step/config/schema = ${ART:-not yet mirrored to pool (in-job path .../ap/8865619b/runs/6ed2c7aa/m$S/artifact.json; its sha follows in the receipt RESULT)}.
- Preparation files (ORDER 0054Z): runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820/config.json b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad; .../prepared/s1_receipt.json a5bbef1b865fd98aa398ded3e31ab60ed40848917646299ffc0ccc15c283ccda; runs/6ed2c7aa/inputs/data_receipt.json 03daaa0a051a72c30e147e20553376e196ad09a183889f243a64a0ab1a212f47 (all under okh7/x_ee227714).
- GCS listing: $(grep '^GCS ' $O/exq.last | cut -c5- | tr '\n' ';' | cut -c1-400)
EOT
echo "$T cont_ops RESULT written" >> $O/log
n=0
while [[ ! -e $O/stop ]]; do
  n=$((n+1)); timeout 1500 bash $OSSH "bash -s $S" < $W/hr2.sh 2>&1 | flt > $O/hr.$n.out; rc=${PIPESTATUS[0]}
  echo "$(date -u +%FT%TZ) hr2 attempt $n rc=$rc" >> $O/log
  [[ $rc == 5 && $n -lt 24 ]] && { sleep ${RETRY:-300}; continue; }
  break
done
T=$(date -u +%Y%m%dT%H%MZ)
{ echo "# RESULT r1_ops (auto, exw.sh): step-$S receipt script attempted on C' (172660); last rc=$rc after $n attempt(s) (0 = every required output published)"
  echo "- Pool dir /project/community/jjyeung/okh7/h_6ed2c7aa/m$S/ now holds: $(grep -o -E '(s\.tar|s\.tar\.failed|RP\.json|h\.json|r\.json|e\.json|DONE\.json)$' $O/hr.$n.out | sort -u | tr '\n' ' '). Local copy of the output: r1_ops6/work/r7/m$S/hr.$n.out."
  grep -E "DONE|ok=|receipt rc|copy rc|mode |NO_STEP|NEAR|BUSY|s.tar$|e.json schema|h.json schema|srun rc" $O/hr.$n.out | head -12 | cut -c1-300 | sed 's/^/- /'
  echo "- Interpretation and the ORDER 0014Z/0209Z follow-up come from the lane's agent."; } > $EV/r1_ops/${T}_RESULT_auto_m${S}_receipts_rc${rc}.md
