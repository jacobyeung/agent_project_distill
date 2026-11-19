#!/bin/bash
# r1_ops7: node-local step monitor (ms_node.sh via ossh) every $(cat mon/sleep2) s; stop file mon/stop2
W=/scratch/jjyeung/orch_n30/r1_ops6/work; M=$W/mon
while [[ ! -e $M/stop2 ]]; do
  { date -u +%FT%TZ; timeout 300 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh 'bash -s' < $W/r7/ms_node.sh 2>&1 | grep -E "^STEP|^H1TOT|rc=|metrics|checkpoint_|/m[0-9]"; } > $M/node.tmp
  grep "^STEP" $M/node.tmp | /scratch/jjyeung/envs/p1cpu/bin/python $W/early_cp.py > $M/node_early.json; echo "early rc=$?" >> $M/node.tmp
  mv $M/node.tmp $M/node_last.txt
  { head -1 $M/node_last.txt | tr '\n' ' '; grep "^STEP" $M/node_last.txt | tail -1 | cut -c1-120; grep -E "early rc|srun rc" $M/node_last.txt | tr '\n' ' '; echo; } >> $M/node_hist.txt
  sleep $(cat $M/sleep2 2>/dev/null || echo 600)
done
