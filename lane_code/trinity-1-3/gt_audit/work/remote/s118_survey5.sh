set -u
cd /scratch/jjyeung/orch_n30 || exit 1
echo "== geo_k1"; ls -la geo_k1 geo_k1/out geo_k1/k1towers 2>&1 | head -60; ls -la geo_k1/harness/out_merged_mdp 2>&1 | head -20
echo "== lift_price"; ls -la b04host3/lift_price/harness 2>&1 | head -60; ls -d b04host3/lift_price/harness/*/ 2>/dev/null; for d in b04host3/lift_price/harness/out*; do [ -d $d ] && { echo "-- $d"; ls -la $d | head -15; }; done
echo "== setsel grep"; grep -n -E "obb|axesLengths|lengths|iou|IoU|overlap" k1_ops3/work/kc_guard/grd_selector/work/setsel/build.py 2>&1 | cut -c1-200 | head -20
echo "== b04 mirror scale"; ls /scratch/jjyeung/n30_mirror/b04_e2ehook/ 2>&1 | head; find /scratch/jjyeung/n30_mirror/b04_e2ehook -maxdepth 5 -iname '*scale*' 2>/dev/null | head -20
