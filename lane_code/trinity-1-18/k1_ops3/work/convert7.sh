#!/bin/bash
# K1 convert phase on CPU (run_k1.sh's command with no card). usage: convert7.sh OWN_ROOT OUT [SECONDS]
set -euo pipefail
OWN=$1; OUT=$2; SEC=${3:-14400}
KC=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/work
MAN=/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json
TOWER=/scratch/jjyeung/k1/run_tower_sam_2; PY=${K1_CONVERT_PY:-/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python}  # = sam3_capretry_native_v1 site-packages + scipy 1.14.1 (orch_cd/evalx/work/trin_vl/pyextra)
echo e684e0c7d8a75e4296e34ba4980aa6d7088f6c2f2053d7850ee790e7cf215146 $MAN | sha256sum -c --strict -
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$OUT/runtime_cache" HF_HOME="$OUT/runtime_cache" TRITON_CACHE_DIR="$OUT/runtime_cache"
echo "CONVERT START $(date -u +%FT%TZ) own=$OWN out=$OUT py=$PY"
"$PY" -I -s -B "$KC/verify_sources.py"
rc=0; nice -n 10 "$PY" -I -s -B "$KC/watchdog.py" --out "$OUT" --stall 900 --seconds "$SEC" -- \
  "$PY" -I -s -B "$KC/k1_pipeline.py" cache --manifest "$MAN" --out "$OUT" --phase convert --max-seconds "$SEC" \
  --preflight-out "$OUT.preflight.json" --tower-cache "$TOWER" --own-cache "$OWN" || rc=$?
echo "CONVERT EXIT rc=$rc $(date -u +%FT%TZ)"
exit $rc
