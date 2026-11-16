set -x
ls /scratch/jjyeung/ | head -80
ls -la /scratch/jjyeung/devs1_mask_run | head -50
ls /scratch/jjyeung/devs1_r2 | head; ls /scratch/jjyeung/devs1_r2/* | head -40
ls /scratch/jjyeung/orch_cd 2>&1 | head -50
ls -la /scratch/jjyeung/orch_cd/o3_cache/out 2>&1 | head -40
ls -la /scratch/jjyeung/orch_cd/devs1_tower/out 2>&1 | head
ls -la /scratch/jjyeung/orch_cd/devs1_direct/out 2>&1 | head
ls -la /scratch/jjyeung/orch_cd/devs1_masks 2>&1 | head -30
