date -u +%FT%TZ
for d in sj fsw rt g3t kit_in feats; do echo "### $d"; find /dev/shm/jjyeung_evalx/$d -maxdepth 4 -type d -printf '%TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null | head -40; done
echo "### milestone"; find /dev/shm/jjyeung_mdg_next/root/orch_cd/evalx/work/milestone -maxdepth 3 -printf '%y %s %TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null | head -60
echo "### sj newest"; find /dev/shm/jjyeung_evalx/sj -type f -newermt 2026-11-12 -printf '%TY-%Tm-%TdT%TH:%TM %s %p\n' 2>/dev/null | sort | tail -30
