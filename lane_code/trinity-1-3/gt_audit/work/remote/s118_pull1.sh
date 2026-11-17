set -u
cd /scratch/jjyeung || exit 1
H=orch_n30/e3_geom/work/harness
A=orch_n30/k1_ops3/work/kc_guard/guard_downstream/analyses
G=orch_n30/k1_ops3/work/e3gd/out
tar cf - \
  orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json \
  orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json \
  orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json orch_cd/k1_build/work/kit_k1a/out/K1_RULES.json \
  orch_cd/k1_build/work/kit_k1a/work/render.py orch_cd/k1_build/work/kit_k1a/work/k1_report.py orch_cd/k1_build/work/kit_k1a/work/k1_pipeline.py orch_cd/k1_build/work/kit_k1a/work/inventory.py orch_cd/k1_build/work/kit_k1a/work/prepare_k1.py orch_cd/k1_build/work/kit_k1a/work/manifest_k1a.py \
  $H/harness.py $H/README.md $H/run.sh $H/agg.py $H/devs1_agg.py $H/devs1_room.py $H/room_rules.py $H/r2fit.py \
  $H/out/PER_ITEM.jsonl $H/out/PER_CAPTURE.jsonl $H/out/FITS.json $H/out/REPORT.md $H/out/RUN_RECEIPT.json $H/out/HELDOUT_TABLE_integrated.txt $H/out/INVENTORY.json $H/out_devs1 \
  $G/PER_ITEM.jsonl $G/PER_CAPTURE.jsonl $G/FITS.json $G/HELDOUT_GD_reviewed.txt $G/HELDOUT_GD_sealed.txt $G/TRAIN_GD_reviewed.txt $G/TRAIN_GD_sealed.txt $G/RUN_RECEIPT.json \
  $A/primary_296/REPORT.json $A/sensitivity_300/REPORT.json $A/primary_296/render/*/responses.json $A/primary_296/refit/FIT_RECEIPT.json \
  orch_n30/k1_ops3/work/k1_split \
  2>/dev/null
