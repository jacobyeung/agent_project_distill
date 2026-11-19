#!/bin/bash
# n_ops1 watcher: one batched Orchard call per interval (mon/sleep, default 60 s; never under 60 s between call starts). Stop: touch mon/stop. Early: touch mon/now.
W=/scratch/jjyeung/orch_n30/n_ops1/work; M=$W/mon; PY=/scratch/jjyeung/envs/p1cpu/bin/python
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
mkdir -p $M/raw
while [[ ! -e $M/stop ]]; do
  t0=$(date +%s); J=$(cat $M/job 2>/dev/null || echo 0)
  if [[ $(cat $M/state_job 2>/dev/null) != "$J" ]]; then [[ -f $M/state.json ]] && mv $M/state.json $M/state.$(date -u +%H%M%S).json; echo "$J" > $M/state_job; fi
  [[ -f $M/state.json ]] || echo "{\"job\": \"$J\"}" > $M/state.json
  MP=$($PY -c "import json;print(json.load(open('$M/state.json')).get('mp','-'))" 2>/dev/null || echo -)
  bash $W/gen.sh "$J" "$MP" $M/cur.sh; had_extra=0; [[ -f $M/extra.sh ]] && had_extra=1
  timeout 300 bash $OSSH 'bash -s' < $M/cur.sh 2>&1 | grep -v -E "WARNING: REMOTE|POSSIBLE|eavesdropping|host key|fingerprint|SHA256:lXw|contact your|google_compute_known|Offending|authentication is disabled|^@@@@" > $M/last.raw
  if (( had_extra )); then st=$(date -u +%H%M%S); awk '/^@@EXTRA/{f=1;next} /^@@END/{f=0} f' $M/last.raw > $M/extra.out.$st; mv $M/extra.sh $M/extra.done.$st; fi
  line=$($PY $W/parse.py $M/last.raw $M); rc=$?
  echo "$line" >> $M/hist.txt; echo "$line" > $M/last.line
  if (( rc != 0 )); then st=$(date -u +%Y%m%dT%H%M%SZ); cp $M/last.raw $M/raw/$st.raw; echo "$st rc=$rc $line" >> $M/ALERTS.txt; fi
  # auto-detect N's launch job: newest j/<id>.out above the last proof, if that job is on advanced
  if [[ $J == 0 ]]; then n=$(grep '^@@NEWEST' $M/last.raw | grep -o '[0-9]*' | head -1)
    if [[ -n $n ]] && (( n > 173236 )) && grep -qE "^$n\|[^|]*\|advanced\|" $M/last.raw; then echo $n > $M/job; echo 60 > $M/sleep; echo "$(date -u +%FT%TZ) autodetect job $n" >> $M/ALERTS.txt; fi
  fi
  iv=$(cat $M/sleep 2>/dev/null || echo 60); (( iv < 60 )) && iv=60
  while (( $(date +%s) - t0 < iv )) && [[ ! -e $M/stop && ! -e $M/now ]]; do sleep 5; done
  [[ -e $M/now ]] && mv $M/now $M/now.used
done
