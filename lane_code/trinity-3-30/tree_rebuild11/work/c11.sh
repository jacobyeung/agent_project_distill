W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; mkdir -p $W/ext/preceipts && tar xzf - -C $W/ext/preceipts && (cd $W/ext/preceipts/rc3 && sha256sum -c --quiet SHA256SUMS.txt && echo SHAOK)
tmux ls | grep tr11; tail -c 300 $W/work/rev20_dispatch.log
ls /scratch/jjyeung/n30_mirror/dist_diag/coverage_v2h/ | head -30
ls -d /scratch/jjyeung/orch_n30/sb_* 2>/dev/null; for d in /scratch/jjyeung/orch_n30/sb_k1list*; do ls $d $d/out 2>/dev/null | head; done
