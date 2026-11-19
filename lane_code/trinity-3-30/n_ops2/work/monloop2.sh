#!/bin/bash
# n_ops2 dual watcher: ONE batched Orchard call per interval covers mon (launch job; n_ops1/work/mon) and mon2 (second job, e.g. the discovery run; n_ops2/work/mon2).
# mon2/job = none -> mon only. Interval = min(mon/sleep, mon2/sleep), never under 60 s. Stop: touch mon/stop. Early: touch mon/now. Extra one-shot: mon/extra.sh (runs in the mon part) or mon2/extra.sh.
W=/scratch/jjyeung/orch_n30/n_ops1/work; M=$W/mon; M2=/scratch/jjyeung/orch_n30/n_ops2/work/mon2; G=/scratch/jjyeung/orch_n30/n_ops2/work/gen2.sh; PY=/scratch/jjyeung/envs/p1cpu/bin/python
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
mkdir -p $M/raw $M2/raw
prep() { local D=$1 J=$2
  if [[ $(cat $D/state_job 2>/dev/null) != "$J" ]]; then [[ -f $D/state.json ]] && mv $D/state.json $D/state.$(date -u +%H%M%S).json; echo "$J" > $D/state_job; fi
  [[ -f $D/state.json ]] || echo "{\"job\": \"$J\"}" > $D/state.json
  MP=$($PY -c "import json;print(json.load(open('$D/state.json')).get('mp','-'))" 2>/dev/null || echo -)
  bash $G "$J" "$MP" $D/cur.sh $D/extra.sh; }
post() { local D=$1 had=$2
  if (( had )); then st=$(date -u +%H%M%S); awk '/^@@EXTRA/{f=1;next} /^@@END/{f=0} f' $D/last.raw > $D/extra.out.$st; mv $D/extra.sh $D/extra.done.$st; fi
  line=$($PY $W/parse.py $D/last.raw $D); rc=$?
  echo "$line" >> $D/hist.txt; echo "$line" > $D/last.line
  if (( rc != 0 )); then st=$(date -u +%Y%m%dT%H%M%SZ); cp $D/last.raw $D/raw/$st.raw; echo "$st rc=$rc $line" >> $D/ALERTS.txt; fi; }
while [[ ! -e $M/stop ]]; do
  t0=$(date +%s); J=$(cat $M/job 2>/dev/null || echo 0); J2=$(cat $M2/job 2>/dev/null || echo none); [[ -z $J2 ]] && J2=none
  prep $M $J; h1=0; [[ -f $M/extra.sh ]] && h1=1; cat $M/cur.sh > $M/both.sh; h2=0
  if [[ $J2 != none ]]; then prep $M2 $J2; [[ -f $M2/extra.sh ]] && h2=1; { echo 'echo @@SPLITJOB'; cat $M2/cur.sh; } >> $M/both.sh; fi
  timeout 300 bash $OSSH 'bash -s' < $M/both.sh 2>&1 | grep -v -E "WARNING: REMOTE|POSSIBLE|eavesdropping|host key|fingerprint|SHA256:lXw|contact your|google_compute_known|Offending|authentication is disabled|^@@@@" > $M/both.raw
  awk '/^@@SPLITJOB/{exit} {print}' $M/both.raw > $M/last.raw; post $M $h1
  if [[ $J2 != none ]]; then awk 'f{print} /^@@SPLITJOB/{f=1}' $M/both.raw > $M2/last.raw; post $M2 $h2; fi
  if [[ $J == 0 ]]; then n=$(grep '^@@NEWEST' $M/last.raw | grep -o '[0-9]*' | head -1)
    if [[ -n $n ]] && (( n > 173236 )) && [[ $n != "$J2" ]] && grep -qE "^$n\|[^|]*\|advanced\|" $M/last.raw; then echo $n > $M/job; echo 60 > $M/sleep; echo "$(date -u +%FT%TZ) autodetect job $n" >> $M/ALERTS.txt; fi
  fi
  iv=$(cat $M/sleep 2>/dev/null || echo 60); if [[ $J2 != none ]]; then i2=$(cat $M2/sleep 2>/dev/null || echo 60); (( i2 < iv )) && iv=$i2; fi; (( iv < 60 )) && iv=60
  while (( $(date +%s) - t0 < iv )) && [[ ! -e $M/stop && ! -e $M/now ]]; do sleep 5; done
  [[ -e $M/now ]] && mv $M/now $M/now.used
done
