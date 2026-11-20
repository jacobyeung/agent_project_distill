W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; O=$W/w24c/out
date -u +%TZ
for f in BUILD24M4D_REPORT.md N_CARD_KIT_ROWS_24M4D.md DELIVERY_24M4D.json arm_routing.py; do echo "@@@ $f $(sha256sum < $O/$f|cut -c1-64)"; cat $O/$f; done
for k in kit_n_go kit_qd; do echo "@@@ $k/SHA256SUMS"; cat $O/$k/SHA256SUMS.txt; cat $O/$k/BUILD.json; echo; done
echo "@@@ rv.py"; cat $O/kit_n_go/b/rv.py
ls $W/w24c/work/build24/kits/ 2>/dev/null
