O=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out; K=$O/kit_n_go/b; date -u +%TZ
sed -n 576,700p $K/z.py | cut -c1-320
grep -n -E "Q_ROOT=|q_22c714e1|x.py|bwrap" $O/kit_n_go/job.sh | head -20 | cut -c1-300
tail -3 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24k/rehearsal_k_run1.log | cut -c1-300
