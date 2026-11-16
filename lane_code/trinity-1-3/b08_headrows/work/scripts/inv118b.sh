cd /scratch/jjyeung
du -sh devs1_mask_run devs1_mask_run/candidates devs1_mask_run/kit devs1_r2/g3s32/g3t devs1_r2/g3s64/g3t devs1_r2/heads_g3s32 orch_cd/devs1_tower/out orch_cd/devs1_direct/out orch_cd/devs1_masks orch_cd/o3_cache orch_cd/devs1_price 2>&1
ls orch_cd/o3_cache orch_cd/o3_cache/*; ls -R orch_cd/devs1_masks | head -40; ls orch_cd/devs1_direct/out; ls -R orch_cd/devs1_tower/out | head -20; ls devs1_mask_run/kit devs1_mask_run/kit/*|head -40; ls devs1_mask_run/candidates | head -5; ls devs1_mask_run/candidates | wc -l
ls devs1_r2/g3s32/g3t | head; ls devs1_r2/g3s32/g3t | wc -l; ls devs1_r2/g3s32/export | head
ls orch_cd/devs1_price; 
echo ======CUE; cat orch_cd/o3_cache/out/CUE_STUDY.md
