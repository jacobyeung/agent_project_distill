W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; cd $W/w24e
ls out; for k in work/build24/kits/q work/build24/kits/n out/kit_n_go out/kit_qd; do echo "$k $(sha256sum $k/SHA256SUMS | cut -c1-64)"; done
sha256sum out/tree_rebuild_b24m4f_26fb868d.tar out/tree_rebuild_b24m4e_737062d4.tar out/arm_routing.py; ls -l out/*.tar
for f in out/BUILD24M4F_REPORT.md out/BUILD24M4E_REPORT.md; do echo "== $f"; head -30 $f | cut -c1-400; done
echo "== USAGE"; cat out/ARM_ROUTING_USAGE.md | cut -c1-600
ls -la work/build24m4d/lane_inputs 2>&1
