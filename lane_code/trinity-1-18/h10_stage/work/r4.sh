K=/scratch/jjyeung/orch_n30/h1_headsft/kit; R=/scratch/jjyeung/orch_n30/review_h10
{ cd $K && du -sh --exclude=tmp . ; du -sh tmp/b8/readk_tmpl 2>/dev/null; du -sh $R/work/tests; ls $K/tests $K/tests/* | head -30; cat $K/cpu.sh; ls /scratch/jjyeung/orch_n30/b04_e2ehook | head; } >&2
