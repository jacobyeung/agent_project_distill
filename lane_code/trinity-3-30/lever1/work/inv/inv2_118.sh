cd /scratch/jjyeung
echo "## g3t"; ls k1/g3t | head -5; ls k1/g3t | wc -l; echo "## partB"; ls k1/partB | head; echo "## src"; ls k1/src | head; echo "## k1_ops3 partb"; ls orch_n30/k1_ops3/work/partb | head; du -s --block-size=1M orch_n30/k1_ops3/work/partb/* 2>/dev/null | sort -rn | head -8
echo "## gt_audit mirror"; ls -la n30_mirror/gt_audit; echo "## sb_kbox4/out"; ls -la orch_n30/sb_kbox4/out | head -30
echo "## sb_k1012"; ls orch_n30/sb_k1012 2>/dev/null; du -s --block-size=1M orch_n30/sb_k1012 orch_n30/b04host3 orch_n30/b04_e2ehook_m544h 2>/dev/null
echo "## e3 harness inputs"; grep -n "scratch\|ROOT\|argparse\|add_argument" orch_n30/e3_geom/work/harness/harness.py | head -40
echo "## e3gd"; ls orch_n30/k1_ops3/work/e3gd orch_n30/k1_ops3/work/e3gd/out | head -40
echo "## e3 harness dir"; ls orch_n30/e3_geom/work/harness | head -40; du -s --block-size=1M orch_n30/e3_geom/work/harness/* | sort -rn | head
echo "## kbox4 run.sh"; cat orch_n30/sb_kbox4/run.sh | head -40
echo "## geo_k1 geom"; ls orch_n30/geo_k1/geom | head -5; ls orch_n30/geo_k1/geom | wc -l
echo "## convert2 sample"; ls k1/run_convert_2/0f21d97647578953
echo "## dose t1_gt"; ls orch_cd/dose_pool/out/t1_gt | head -5; ls orch_cd/dose_pool/out/t1_gt/gt 2>/dev/null | wc -l; ls orch_cd/dose_pool/out/arkit_gt/gt 2>/dev/null | wc -l; ls orch_n30/gt_build/out/dose_pool/out/t1_gt/gt 2>/dev/null | wc -l; ls orch_n30/gt_build/out/dose_pool/out/arkit_gt/gt 2>/dev/null| wc -l
