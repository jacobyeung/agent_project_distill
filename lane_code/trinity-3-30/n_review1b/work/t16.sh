W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24; K=$W/out/kit_qd
cat $W/out/BUILD24M2D_REPORT.md $W/out/MISSING_STAGED_PINS.md
grep -n "RECONSTRUCT\|reconstruct\|4e8e6c04" $K/b/*.py | head -30
