exec 3>&1 1>&2
C=/scratch/jjyeung/orch_n30/cont_ops24_c/cap
ls -la $C/t1ret $C/score_t1; tail -2 /scratch/jjyeung/orch_n30/cont_ops25_c/r7_run.log; uptime
cd $C && tar cf - t1ret >&3
