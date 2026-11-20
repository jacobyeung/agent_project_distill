W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; E=$W/w24e
date -u +%TZ; ls $E/out | head -50; ls $E/work/build24/kits/ 2>&1
for k in out/kit_n_go out/kit_qd work/build24/kits/n work/build24/kits/q; do echo "@@@ $k $(sha256sum < $E/$k/SHA256SUMS.txt | cut -c1-64)"; cat $E/$k/SHA256SUMS.txt; done
echo "@@@ arm_routing.py $(sha256sum < $E/out/arm_routing.py|cut -c1-64)"; cat $E/out/arm_routing.py
