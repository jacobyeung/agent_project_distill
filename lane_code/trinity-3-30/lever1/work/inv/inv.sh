set -u
echo "HOST $(hostname -s) $(date -u +%FT%TZ)"; df -h /scratch | tail -1
cd /scratch/jjyeung || exit 0
echo "## top"; ls
for d in k1 orch_n30 n30_mirror orch_cd; do [ -d $d ] && { echo "## $d"; timeout 120 du -s --block-size=1M $d/* 2>/dev/null | sort -rn | head -60; }; done
for d in k1/run_convert_2 k1/m544_parts orch_n30/geo_k1 orch_n30/geo_k1/pred_gpu orch_n30/e3_geom/work orch_n30/k1_ops3/work orch_n30/gt_build/out orch_n30/gt_build/out/dose_pool/out orch_cd/dose_pool/out orch_n30/gt_audit/out orch_n30/sb_kbox4 n30_mirror/cont_ops24 n30_mirror/cont_ops25; do [ -d $d ] && { echo "## $d"; timeout 60 du -s --block-size=1M $d/* 2>/dev/null | sort -rn | head -25; }; done
