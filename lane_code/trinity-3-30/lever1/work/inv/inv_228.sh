echo "HOST $(hostname -s) $(date -u +%FT%TZ)"; df -h /scratch | tail -1; free -g | head -2; nproc; uptime
tmux ls 2>&1 | head -20
cd /scratch/jjyeung || exit 0
ls; ls orch_n30; du -s --block-size=1M orch_n30/* n30_mirror/* 2>/dev/null | sort -rn | head -30
for d in orch_n30/cont_ops25_c orch_n30/cont_ops24_c orch_n30/grd_funnel1 orch_n30/cont_ops25_c/cam orch_n30/cont_ops24_c/gbuild orch_n30/cont_ops24_c/gbuild/cap; do echo "## $d"; ls $d 2>/dev/null | head -40; done
ls orch_n30/cont_ops25_c/cam/gt/t1_gt/gt 2>/dev/null | wc -l
ls -la orch_n30/cont_ops24_c/gbuild/cap/*.gz 2>/dev/null
