hostname -s; cut -d' ' -f1-3 /proc/loadavg; df -h /scratch | tail -1
cd /scratch/jjyeung/n30_mirror && ls
for d in rows_r1 count_diag r1_pkt r1_ops cont_ops tree_rebuild_w rows_a2; do echo "== $d"; ls $d 2>&1 | head -20; done
ls -la rows_r1/out 2>/dev/null | head; ls -la rows_r1/out/a2_vqa_v7 2>/dev/null | head
