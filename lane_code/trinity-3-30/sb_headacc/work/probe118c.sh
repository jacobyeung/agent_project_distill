H=/scratch/jjyeung/orch_n30/b04host3/lift_price/harness
echo "## run.sh"; cat $H/run.sh | cut -c1-400 | head -30
echo "## lift_price.py head"; sed -n '1,43p' $H/lift_price.py | cut -c1-220
echo "## reader_distance"; sed -n '150,215p' $H/lift_price.py | cut -c1-220
echo "## sha"; sha256sum $H/lift_price.py $H/harness.py $H/agg.py | cut -c1-80
echo "## out_lift_train"; ls $H/out_lift_train_v2 | head -4; ls $H/out_lift_train_v2 | wc -l
S=/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector
echo "## selector"; ls $S/data/caps_raw | head -3; ls $S/data/caps_raw | wc -l; ls $S/data/caps_iso | head -3; ls $S/data/caps_iso | wc -l; ls $S/work/run_iso | head; sed -n '1,25p' $S/SELECTOR_HEAD_REPORT.md | cut -c1-500
echo "## mirrors"; ls /scratch/jjyeung/n30_mirror/ | tr '\n' ' '; echo; ls /scratch/jjyeung/n30_mirror/gt_audit /scratch/jjyeung/n30_mirror/tower_redecide 2>&1 | head -30
echo "## r0"; ls /scratch/jjyeung/orch_n30/b10_reserve/out/qsets | head -20; ls /scratch/jjyeung/orch_n30/b10_reserve/frames/scannetpp | wc -l; ls /scratch/jjyeung/orch_n30/b10_reserve/out | head -30
echo "## k1 frames"; ls /scratch/jjyeung/k1_frames | head -3; ls /scratch/jjyeung/k1_frames | wc -l
echo "## devs1"; ls /scratch/jjyeung/devs1_r2/anchors | head -3; ls /scratch/jjyeung/devs1_r2/g3s32 | head -5; ls /scratch/jjyeung/devs1_r2/g3s64 | head -5; ls /scratch/jjyeung/devs1_frames/00 | head -3
echo "## geo kit"; ls /scratch/jjyeung/geo_bakeoff_kit | head -12
