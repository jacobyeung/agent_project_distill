#!/bin/bash
# Run on trinity-1-3 after all six parts and parity.jsonl exist on Orchard. Pulls small result files one at a time, then seals.
set -euo pipefail
L=/scratch/jjyeung/orch_n30/b06_a2dense; O=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
R=/project/community/jjyeung/okh7/db3954b2; D=$L/work/fetch_out; mkdir -p $D
echo "ls -la $R/parts/*/DONE $R/parity.jsonl; wc -c $R/parts/*/out.jsonl" | timeout 300 bash $O 'bash -s' > $D/inventory.txt
timeout 300 bash $O "cat $R/parts/a*/out.jsonl" > $D/wa_out.jsonl; sleep 30
timeout 300 bash $O "cat $R/parts/v*/out.jsonl" > $D/wd_out.jsonl; sleep 30
timeout 300 bash $O "cat $R/parity.jsonl" > $D/parity.jsonl
sha256sum $D/*.jsonl > $D/SHA256SUMS
B06_TREE=$L/cache/work/tree_r1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $L/dense/dense_manifest.py seal $L/out/plan_v4 $D/wd_out.jsonl $D/wa_out.jsonl $D/SEALED.json $D/parity.jsonl | tee $D/seal_summary.json
