#!/bin/bash
# At GO, on trinity-3-30: bash run_go.sh NEW_TREE_DIR NEW_SEAL NEW_TAR_SHA256 LABEL
# Step 1 (local): prep.sh; step 2 (Orchard call 1): upload s29r.tar as X/s29r.tar.part; step 3 (Orchard call 2, >=2 min later): o_go.sh with SUBMIT=1.
set -euo pipefail
F=/scratch/jjyeung/orch_n30/tree_rebuild29/work/fix22; OS=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
L=$4; bash $F/s/prep.sh "$@"; O=$F/pkg/$L
echo "{\"utc\":\"$(date -u +%FT%TZ)\",\"lane\":\"tree_rebuild29\",\"who\":\"fix22\",\"meaning\":\"upload s29r.tar (mode r candidate delta, $(stat -c %s $O/s29r.tar) B) to X/s29r.tar.part\"}" >> $F/../ORCHARD_LEDGER.jsonl
echo "call $(date -u +%FT%TZ) upload s29r.tar" >> $F/s/CALLS.log
timeout 300 bash $OS "cat > /project/community/jjyeung/okh7/x_22c714e1/s29r.tar.part && sha256sum /project/community/jjyeung/okh7/x_22c714e1/s29r.tar.part" < $O/s29r.tar | tee $O/upload.out
grep -q "$(cut -c1-64 $O/s29r.tar.sha256)" $O/upload.out || { echo UPLOAD_SHA_MISMATCH; exit 1; }
sleep 125
echo "{\"utc\":\"$(date -u +%FT%TZ)\",\"lane\":\"tree_rebuild29\",\"who\":\"fix22\",\"job_name\":\"a15_cot_apd1efc29326c7\",\"meaning\":\"CPU preempt rcj mode r on candidate folder $(python3 -c "import json;print(json.load(open('$O/PREP.json'))['folder'])") (new tree, regenerated selection)\"}" >> $F/../ORCHARD_LEDGER.jsonl
echo "call $(date -u +%FT%TZ) o_go SUBMIT=1" >> $F/s/CALLS.log
(echo SUBMIT=1; cat $O/o_go.sh) | timeout 300 bash $OS 'bash -s' 2>&1 | tee $O/o_go.out
