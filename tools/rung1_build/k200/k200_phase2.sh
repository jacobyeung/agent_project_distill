#!/bin/bash
# Phase 2: upload the prep specs and submit the CPU preps (32 CPUs, 240G) on closure f344aa6b; X9W64 waits for X9.
R=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes/rung1_build_20261027
PY=/home/jjyeung/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12
D=/scratch/jjyeung/rung1_push/k200
CL=f344aa6ba407a39f5716fb665757007f0b62dd8ace1d397d1697dd11642a3890
cd $R/tools || exit 1
for s in SPEC_K200_R27X:6:00:00 SPEC_K200_X9:5:00:00 SPEC_K200_R27A1:4:00:00 SPEC_K200_W64:4:00:00 SPEC_K200_A1S18:4:00:00; do
  name=${s%%:*}; limit=${s#*:}
  d=$($PY -B r1actions.py spec $D/$name.json)
  n=$($PY -B r1actions.py sbatch $CL $d 32 240G $limit)
  echo "$name spec ${d:0:12} job_name $n limit $limit"
done
for t in 1 2 3; do timeout 600 env R1_MIN_INTERVAL=55 $PY -B r1aws.py run 2>&1 | tail -1 | cut -c1-100; sleep 5; [ -z "$(ls $R/actions/pending | grep '^f_')" ] && break; sleep 55; done
grep -h "SBATCH_REPLY\|NOT_SUBMITTED\|REFUSED" $(ls -t $R/polls/poll_*.txt | head -3) | sort -u | cut -c1-200
