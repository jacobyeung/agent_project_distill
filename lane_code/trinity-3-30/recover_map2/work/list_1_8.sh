hostname -s; date -u +%FT%TZ; df -h /scratch /dev/shm
echo "## scratch depth1"; ls -la /scratch/jjyeung 2>&1
echo "## orch_cd depth3"; find /scratch/jjyeung/orch_cd -maxdepth 3 -printf '%y %s %TY-%Tm-%TdT%TH:%TM %p\n' 2>&1 | head -400
echo "## evalx_native_transfer"; find /scratch/jjyeung/evalx_native_transfer_20261114 -maxdepth 2 -printf '%y %s %TY-%Tm-%TdT%TH:%TM %p\n' 2>&1 | head -60
echo "## mdg_next_sam3"; ls -la /scratch/jjyeung/mdg_next_sam3 2>&1 | head
echo "## shm evalx"; find /dev/shm/jjyeung_evalx -maxdepth 3 -printf '%y %s %TY-%Tm-%TdT%TH:%TM %p\n' 2>&1 | head -200
echo "## du"; du -s /scratch/jjyeung/orch_cd/* /dev/shm/jjyeung_evalx/* 2>/dev/null | head -60
