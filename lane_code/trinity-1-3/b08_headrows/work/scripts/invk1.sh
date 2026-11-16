cd /scratch/jjyeung/k1; ls; for d in *; do echo "== $d"; ls $d | head -25; done; du -sh /scratch/jjyeung/k1/* 2>/dev/null
ls /scratch/jjyeung/mask_recall_run/results/dense_aliases/priced 2>&1 | head
ls /scratch/jjyeung/orch_n30 | head -60
