cd /scratch/jjyeung/orch_n30/native_r2/work || exit 1
ls np226 base streams meta | head -40
ls /scratch/jjyeung/ | head -40
ls /scratch/jjyeung/mask_recall_run 2>/dev/null | head
for d in np226/*; do echo "$d $(ls $d | head -3 | tr '\n' ' ')"; done
ls -la /dev/shm/jjyeung 2>/dev/null | head
