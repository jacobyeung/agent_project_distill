#!/bin/bash
# K1 tower_sam phase on one card under vnice (run inside tmux k1gpu). usage: launch_tower_sam.sh CARD
set -u
CARD=$1; KC=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a
MAN=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_finalize_v2/K1_MANIFEST.finalized.json
OUT=/scratch/jjyeung/k1/run_tower_sam; PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python
echo "LAUNCH $(date -u +%FT%TZ) card=$CARD manifest_sha=$(sha256sum $MAN | cut -c1-64)" >> /scratch/jjyeung/k1/RUN.log
bash $KC/work/run_k1.sh trinity-1-18 $CARD $MAN $OUT /scratch/jjyeung/k1/tools/vnice.sh $PY tower_sam 14400 >> /scratch/jjyeung/k1/RUN.log 2>&1
echo "EXIT rc=$? $(date -u +%FT%TZ)" >> /scratch/jjyeung/k1/RUN.log
