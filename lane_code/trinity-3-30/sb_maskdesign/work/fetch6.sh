K1=/scratch/jjyeung/k1
echo "=== t4.sh"; head -c 2500 $K1/t4.sh; echo; echo "=== src tree"; find $K1/src -maxdepth 4 | head -40
d=$(ls $K1/run_tower_sam_2 | head -1); echo "=== PHASE_COMPLETE $d"; head -c 4200 $K1/run_tower_sam_2/$d/PHASE_COMPLETE.json; echo
echo "=== candidates.json head"; head -c 1500 $K1/run_tower_sam_2/$d/candidates.json; echo
echo "=== RUN2.log head"; head -c 1500 $K1/RUN2.log; echo
echo "=== gt stores"; for x in /scratch/jjyeung/orch_n30/gt_rasters /scratch/jjyeung/orch_n30/gt_build2 /scratch/jjyeung/n30_mirror/b12_cntapp /scratch/jjyeung/n30_mirror/b05_owngrd; do echo "-- $x"; ls -la $x | head -25; [ -f $x/STATUS.md ] && head -c 2500 $x/STATUS.md; done
echo "=== kobj4 gpu plan"; ls /scratch/jjyeung/orch_n30/sb_kobj4/out 2>/dev/null | head -30; for f in /scratch/jjyeung/orch_n30/sb_kobj4/out/GPU_PLAN.md /scratch/jjyeung/orch_n30/sb_kobj4/out/REPORT.md; do [ -f $f ] && { echo "-- $f"; head -c 3500 $f; }; done
echo "=== sam3 locations"; ls -d /scratch/jjyeung/*/sam3* /scratch/jjyeung/orch_n30/*/sam3* /scratch/jjyeung/models/* 2>/dev/null | head -20; ls /scratch/jjyeung/trinity_qwen_sam3 | head; grep -rn "sam3" $K1/t4.sh $K1/tools/*.sh 2>/dev/null | cut -c1-240 | head -12
