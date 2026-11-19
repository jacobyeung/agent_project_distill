W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W && tar xzf - -C $W && ls ext/pk | wc -l
date -u +%TZ; tmux ls | grep tr10; tail -c 1500 $W/w15/work/build15/STATUS.md; ls $W/w15/out | grep -i 15
I=$W/w14/work/n1fix2/inputs; echo "== row_sources"; head -c 3000 $I/row_sources.json; echo; echo "== mix"; head -c 4000 $I/mix.json; echo; echo "== v7_receipt"; head -c 1500 $I/v7_receipt.json; echo; ls -la $I | head -60
echo "== kits r1"; ls $W/w14/work/build14/kits/r1 | head -30; ls /scratch/jjyeung/n30_mirror/rows_r1/out /scratch/jjyeung/n30_mirror/rows_r1/out/vehN_units/repaired /scratch/jjyeung/n30_mirror/rows_r1/out/recovery_v3 /scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full /scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/repaired 2>&1 | head -60
