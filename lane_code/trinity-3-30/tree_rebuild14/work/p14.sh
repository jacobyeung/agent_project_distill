date -u +%TZ; K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go
grep -n -E "TK_JOB_START|Q_ROOT=|Q_NS=|Q_KIT=|HX=|TK_KIT_HOME|HM=" /tmp/tr14_j.sh $K/b/z.py $K/b/e.sh </dev/null | cut -c1-200 | head -20
cat $K/b/e.sh </dev/null | head -20
python3 -B /tmp/tr14_dec.py /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24d/go/v.json output,preparation_output </dev/null
