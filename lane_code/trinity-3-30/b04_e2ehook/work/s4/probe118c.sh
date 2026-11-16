B=/scratch/jjyeung/orch_n30/b04host/b04_e2ehook
cat $B/work/host_run2.sh | cut -c1-400 | head -30; echo ---; head -5 $B/work/restore.log | cut -c1-300
ls -la /scratch/jjyeung/orch_cd/ttower/work/sam3_weights 2>&1 | head; ls /scratch/jjyeung/orch_n30/b05_owngrd/work 2>&1 | head -30
ls /scratch/jjyeung/orch_n30/ | head -80 | tr '\n' ' '
