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


# F2: the sets are the frozen ones of amendment 1, and kc carries the reviewed deployment.
sha256sum -c --strict - <<SUMS
2b82af5241db3c8048e9998f766b5dcd24accdaab93bbd8a169aefba39a1f121  $GTSETS/GT_SET_PRIMARY_296.json
e305c4be0d604df277d06e7d9b1e13893dfa659d7ab6663f0de798773d58d650  $GTSETS/GT_SET_SENSITIVITY_300.json
5d36d1ea98c14b2e3181a4571a87dc81efa980bd88a2302e27a1ecc13833a4f8  $KIT/work/gt_set.py
f14df4eda722337e0e7187a759e287eed79bb3201b03ffef351591ce5241c0da  $KIT/work/k1_cli.py
deb51a265425e092870c7eadb2fd498b5942b466bb759b39c84fa96e0c762157  $KIT/work/k1_pipeline.py
14b35f83184267f85a946079767d7903d3e1c31d73946bd2600bbe6b2efe862d  $KIT/work/k1_report.py
4087716014ab26e7fdb91f336e3d8ee81f97e82b85a4c340376e872c655ecfef  $KIT/work/refit/train.py
aa0a728148bbf076fe1d42a6fe4bb053c761052ec653faa02f7a06e240b8ca42  $KIT/out/DEPENDENCIES.json
SUMS
grep -q 2b82af5241db3c8048e9998f766b5dcd24accdaab93bbd8a169aefba39a1f121 /data2/jjyeung/agent_project_data/distill_design/REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md
grep -q e305c4be0d604df277d06e7d9b1e13893dfa659d7ab6663f0de798773d58d650 /data2/jjyeung/agent_project_data/distill_design/REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md

# R1: tables read the original convert root; every file a CACHE_COMPLETE pins lies under it.
nice -n 10 "$PY" -B - "$K1_CONVERT_CACHE" <<'PYEOF'
import json,os,sys
from pathlib import Path
root=Path(os.path.realpath(sys.argv[1]))
b=json.load(open(root/'BINDING.json'))
if b.get('phase')!='convert':raise SystemExit(f'R1: {root} is not a convert root (phase {b.get("phase")})')
n=0
for d in sorted(root.iterdir()):
    r=d/'CACHE_COMPLETE.json'
    if not r.is_file():continue
    for pin in json.load(open(r))['files'].values():
        p=Path(os.path.realpath(pin['path'] if isinstance(pin,dict) else pin))
        if root not in p.parents:raise SystemExit(f'R1: {r} pins {p} outside {root}')
    n+=1
print(f'R1 ok: {n} CACHE_COMPLETE receipts, all pinned files under {root}')
PYEOF

# R2: MODE=r2 K1_R2_CAPTURE=<canonical> tables one real capture of the primary set into analyses/r2_<utc>/ and stops.
if [ "${MODE:-full}" = r2 ]; then
  : "${K1_R2_CAPTURE:?Set K1_R2_CAPTURE to one canonical of the primary set}"
  R2="$BUILD/analyses/r2_$(date -u +%Y%m%dT%H%M%SZ)"; mkdir -p "$R2"
  nice -n 10 "$PY" -B -c 'import json,sys;s=json.load(open(sys.argv[1]));c=sys.argv[2];json.dump({c:s[c]},open(sys.argv[3],"w"),indent=1,sort_keys=True)' "$GTSETS/GT_SET_PRIMARY_296.json" "$K1_R2_CAPTURE" "$R2/GT_SET_R2.json"
  nice -n 10 "$PY" -B "$KIT/work/k1_pipeline.py" tables --manifest "$MANIFEST" --cache "$K1_CONVERT_CACHE" --gt-set "$R2/GT_SET_R2.json" --out "$R2/tables"
  cat "$R2/tables/TABLE_RECEIPT.json"; exit 0
fi
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
