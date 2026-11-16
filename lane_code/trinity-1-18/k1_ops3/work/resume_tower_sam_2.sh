#!/bin/bash
# Resume K1 tower_sam in run_tower_sam_2 after the reviewed --max-bytes fix (run inside tmux k1gpu2b). usage: resume_tower_sam_2.sh CARD
set -eu
CARD=$1; KC=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a; F=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_maxbytes
MAN=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
OUT=/scratch/jjyeung/k1/run_tower_sam_2; PY=/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python; LOG=/scratch/jjyeung/k1/RUN2b.log
[ "$(sha256sum $KC/work/k1_cli.py | cut -c1-64)" = 3cc7b95ff591d68dc0184ac76d7b706a3b7920c94a2132b0eedd99c1c7e49013 ]
[ "$(sha256sum $KC/out/DEPENDENCIES.json | cut -c1-64)" = b27c28c4fc8c32299dda66d470644c7f6d1b574492fe81a767e601f1b47b91e2 ]
echo "RESUME $(date -u +%FT%TZ) card=$CARD manifest_sha=$(sha256sum $MAN | cut -c1-64)" >> $LOG
set +e
bash $KC/work/run_k1.sh trinity-1-18 $CARD $MAN $OUT /scratch/jjyeung/k1/tools/vnice.sh $PY tower_sam 14400 --max-bytes 4000000000 >> $LOG 2>&1
echo "EXIT rc=$? $(date -u +%FT%TZ)" >> $LOG
