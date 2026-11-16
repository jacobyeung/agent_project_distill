cd /scratch/jjyeung
du -sh devs1_r2/heads_g3s32_vcd devs1_r2/heads_g3s64_vcd
tar cf - devs1_r2/heads_g3s32_vcd devs1_r2/heads_g3s64_vcd devs1_r2/g3s32/export devs1_r2/g3s64/export | ssh -o ConnectTimeout=20 trinity-1-3.ib "cd /scratch/jjyeung/orch_n30/b08_headrows/work/src118 && tar xf -"
echo TAR_RC $?
ls /scratch/jjyeung/envs
