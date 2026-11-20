exec 3>&1 1>&2
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild; C=/scratch/jjyeung/orch_n30/cont_ops24_c/cap
ls -la $C/score_t1; wc -c $G/REPORT7.md
cd / && tar czf - $G/REPORT7.md $G/SHA256SUMS7 $C/score_t1/*.md >&3
