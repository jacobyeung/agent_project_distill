cd /scratch/jjyeung/orch_cd
echo ==probe; ls own_probe/out | head -80
echo ==mdg; ls mdg_build/work | head -80; ls mdg_build/work/t0bundle/base mdg_build/work/weights | head -30
echo ==gt; ls dose_pool/out/t1_gt/gt | wc -l; ls dose_pool/out/arkit_gt/gt | wc -l; ls dose_pool/out/t1_gt | head; ls dose_pool/out/t1_gt/gt | head -3; du -sh dose_pool/out/t1_gt/gt dose_pool/out/arkit_gt/gt
echo ==mdgnext; ls mdg_next/work mdg_next/work/out | head -40
