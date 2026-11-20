W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24
ls -lt $W/out | head -25
ls $W/out/kit_qd $W/out/kit_qd/b 2>&1 | head -50
for f in $W/out/jd2.sh $W/out/dbb2.py $W/out/kit_qd/b/rg.py $W/out/kit_qd/b/a.py $W/out/kit_qd/b/rd.py $W/out/kit_qd/job.sh; do [ -f $f ] && { echo "=== $f $(sha256sum < $f | cut -c1-16)"; cat $f; }; done
