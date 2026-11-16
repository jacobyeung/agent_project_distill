#!/usr/bin/env bash
# Run only after independent review and deployment, after tower_sam has ended.
# This file does not deploy or change phase artifacts.
set -euo pipefail
: "${K1_CONVERT_CACHE:?Set this to the completed convert output root, not the tower_sam root}"
: "${K1_REFIT_PY:?Set this to an approved CPU Python with numpy and scikit-learn}"

BUILD=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset
KIT=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a
MANIFEST=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
GTSETS=/scratch/jjyeung/orch_n30/k1_ops3/work/gt_sets
PY=/scratch/jjyeung/envs/p1cpu/bin/python
export CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$BUILD/runtime_cache" HF_HOME="$BUILD/runtime_cache/hf" TRITON_CACHE_DIR="$BUILD/runtime_cache/triton"
cd "$BUILD"

# These are existing refit prerequisites, not part of this patch.
test -f /scratch/jjyeung/orch_n30/k1_ops3/kc/grd_selector/work/setsel/setlib.py
test -f /scratch/jjyeung/orch_n30/k1_ops3/kc/devs1_masks/out/kit/work/vendor/MODELS.json
nice -n 10 "$K1_REFIT_PY" -B -c 'import numpy, sklearn'
nice -n 10 "$PY" -B "$KIT/work/verify_sources.py"
INVENTORY=$(nice -n 10 "$PY" -B -c 'import json,sys;print(json.load(open(sys.argv[1]))["inventory"]["path"])' "$MANIFEST")

PRIMARY="$BUILD/analyses/primary_296"
SENSITIVITY="$BUILD/analyses/sensitivity_300"

nice -n 10 "$PY" -B "$KIT/work/k1_pipeline.py" tables --manifest "$MANIFEST" --cache "$K1_CONVERT_CACHE" --gt-set "$GTSETS/GT_SET_PRIMARY_296.json" --out "$PRIMARY/tables"
nice -n 10 "$K1_REFIT_PY" -B "$KIT/work/refit/train.py" --candidates "$PRIMARY/tables/candidates.jsonl" --pairs "$PRIMARY/tables/pairs.jsonl" --inventory "$INVENTORY" --gt-set "$GTSETS/GT_SET_PRIMARY_296.json" --out "$PRIMARY/refit"
nice -n 10 "$PY" -B "$KIT/work/k1_pipeline.py" render --manifest "$MANIFEST" --cache "$K1_CONVERT_CACHE" --fit "$PRIMARY/refit" --gt-set "$GTSETS/GT_SET_PRIMARY_296.json" --out "$PRIMARY/render"
nice -n 10 "$PY" -B "$KIT/work/k1_report.py" --rows "$PRIMARY/render/K1_ANALYSIS_INPUT.jsonl" --inventory "$INVENTORY" --manifest "$MANIFEST" --fit "$PRIMARY/refit/FIT_RECEIPT.json" --ids-from "$PRIMARY/tables/TABLE_RECEIPT.json" --gt-set "$GTSETS/GT_SET_PRIMARY_296.json" --out "$PRIMARY/REPORT.json"

nice -n 10 "$PY" -B "$KIT/work/k1_pipeline.py" tables --manifest "$MANIFEST" --cache "$K1_CONVERT_CACHE" --gt-set "$GTSETS/GT_SET_SENSITIVITY_300.json" --sensitivity --out "$SENSITIVITY/tables"
nice -n 10 "$K1_REFIT_PY" -B "$KIT/work/refit/train.py" --candidates "$SENSITIVITY/tables/candidates.jsonl" --pairs "$SENSITIVITY/tables/pairs.jsonl" --inventory "$INVENTORY" --gt-set "$GTSETS/GT_SET_SENSITIVITY_300.json" --sensitivity --out "$SENSITIVITY/refit"
nice -n 10 "$PY" -B "$KIT/work/k1_pipeline.py" render --manifest "$MANIFEST" --cache "$K1_CONVERT_CACHE" --fit "$SENSITIVITY/refit" --gt-set "$GTSETS/GT_SET_SENSITIVITY_300.json" --sensitivity --out "$SENSITIVITY/render"
nice -n 10 "$PY" -B "$KIT/work/k1_report.py" --rows "$SENSITIVITY/render/K1_ANALYSIS_INPUT.jsonl" --inventory "$INVENTORY" --manifest "$MANIFEST" --fit "$SENSITIVITY/refit/FIT_RECEIPT.json" --ids-from "$SENSITIVITY/tables/TABLE_RECEIPT.json" --gt-set "$GTSETS/GT_SET_SENSITIVITY_300.json" --sensitivity --out "$SENSITIVITY/REPORT.json"
