echo "== $(hostname -s) $(date -u +%T)"
for d in /scratch/jjyeung/devs1_frames /scratch/jjyeung/orch_n30/trin_read/root/k6tk/parts /scratch/jjyeung/orch_n30/sb_framepool/work; do echo "-- $d"; ls $d 2>&1 | head -3; ls $d 2>/dev/null | wc -l; done
find /scratch/jjyeung/devs1_frames -type f 2>/dev/null | wc -l
du -sh /scratch/jjyeung/orch_n30/trin_read/root/k6tk/parts 2>/dev/null
ls /scratch/jjyeung/ | head -50
