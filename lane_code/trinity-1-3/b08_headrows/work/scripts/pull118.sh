cd /scratch/jjyeung
ls devs1_mask_run/kit/work devs1_mask_run/kit/work/out 2>&1 | head -60
ls devs1_r2/heads_g3s64 | wc -l; du -sh devs1_r2/heads_g3s64 devs1_r2/anchors devs1_r2/g3s32/export devs1_r2/g3s64/export
ls orch_cd/devs1_direct/out/r2 orch_cd/devs1_direct/out/r5 | head -30
ls orch_cd/o3_cache/work/kit | head -30
ls k1 | head -30
tar cf - devs1_mask_run devs1_r2/g3s32/g3t devs1_r2/g3s64/g3t devs1_r2/heads_g3s32 devs1_r2/heads_g3s64 devs1_r2/anchors devs1_r2/REQUEST.json devs1_r2/COMPLETE.json orch_cd/devs1_tower orch_cd/devs1_direct orch_cd/devs1_masks orch_cd/o3_cache orch_cd/devs1_price | ssh -o ConnectTimeout=20 trinity-1-3.ib "mkdir -p /scratch/jjyeung/orch_n30/b08_headrows/work/src118 && cd /scratch/jjyeung/orch_n30/b08_headrows/work/src118 && tar xf -"
echo TAR_RC $?
