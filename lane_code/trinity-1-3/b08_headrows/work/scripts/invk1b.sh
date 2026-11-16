cd /scratch/jjyeung/orch_n30
for d in e3_geom k1_rules k1_ops5 gt_rasters; do echo "== $d"; ls $d; ls $d/out $d/work 2>/dev/null | head -40; done
ls /scratch/jjyeung/k1/run_tower_sam_2/01949c4249271126
ls /scratch/jjyeung/k1/run_tower_sam_2 | wc -l
cat /scratch/jjyeung/k1/T4_STATUS.txt | tail -5
