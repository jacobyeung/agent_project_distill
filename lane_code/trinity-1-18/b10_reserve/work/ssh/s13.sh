hostname -s
cd /scratch/jjyeung/orch_n30 2>/dev/null && ls
echo ==== pull
ls -la /scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull/m/ 2>&1 | head -80
find /scratch/jjyeung/orch_n30/rows_rebuild/work/s0/pull -maxdepth 4 | head -150
