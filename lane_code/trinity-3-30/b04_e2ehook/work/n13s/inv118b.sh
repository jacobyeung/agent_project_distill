cd /scratch/jjyeung/orch_cd || exit 1
timeout 120 find evalx/work/milestone legs1_reads leg_s1_tree -maxdepth 7 \( -name 's1_receipt.json' -o -path '*prepare_dd26bb95*' -o -name 'data_receipt.json' -o -name 'FRAMES.json' -o -name 'MASK_CACHE_C8_BOUND.json' \) 2>/dev/null | head -30
echo ==; ls evalx/work/milestone 2>&1 | head -40
echo ==; ls -la /scratch/jjyeung/devs1_frames | head -5; ls /scratch/jjyeung/devs1_frames | wc -l; du -sh /scratch/jjyeung/devs1_frames /scratch/jjyeung/k1/g3t 2>&1; ls -la /scratch/jjyeung/k1/g3t
