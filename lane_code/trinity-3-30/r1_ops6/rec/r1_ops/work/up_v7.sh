#!/bin/bash
O=/project/community/jjyeung/okh7/s_22b44165
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
cd /scratch/jjyeung/orch_n30/r1_ops/work
/usr/bin/python3 -s /scratch/jjyeung/orch_n30/r1_ops/work/gpush.py r1_ops_store_v7 /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite -- timeout 3600 bash $OSSH "umask 077; mkdir -p -m 700 $O && cat > $O/d.db.part && mv $O/d.db.part $O/d.db && chmod 400 $O/d.db && sha256sum $O/d.db && ls -la $O"
echo "EXIT $?"
