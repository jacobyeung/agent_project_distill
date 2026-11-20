E=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24e/out
for f in a.py h.py o.py pl.py rv.py; do echo "@@@ $f"; diff -u $E/kit_qd/b/$f $E/kit_n_go/b/$f | head -150; done
echo "@@@ job.sh"; diff -u $E/kit_qd/job.sh $E/kit_n_go/job.sh | head -60
