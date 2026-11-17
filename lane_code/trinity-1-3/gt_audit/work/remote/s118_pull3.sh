set -u
cd /scratch/jjyeung || exit 1
tar cf - --ignore-failed-read \
  orch_n30/geo_k1/k1towers/decide.py orch_n30/geo_k1/k1towers/merge_caps.py orch_n30/geo_k1/k1towers/k1_price.py orch_n30/geo_k1/k1towers/agg.py orch_n30/geo_k1/k1towers/GEO_TOWERS_K1_PREREG_20261116.md \
  orch_n30/geo_k1/out orch_n30/geo_k1/harness/out_merged_mdp \
  orch_n30/b04host3/lift_price/harness/AGG_HELDOUT_reg.txt orch_n30/b04host3/lift_price/harness/AGG_TRAIN.txt orch_n30/b04host3/lift_price/harness/AGG_TRAIN_v2.txt orch_n30/b04host3/lift_price/harness/agg.py orch_n30/b04host3/lift_price/harness/lift_price.py orch_n30/b04host3/lift_price/harness/out_lift_heldout_reg \
  n30_mirror/b04_e2ehook/b04_e2ehook/heads/scale \
  orch_n30/k1_ops3/work/kc_guard/grd_selector/work/setsel/build.py
