W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
T=$W/w26fix/tree
echo "== exists w26fix2:"; ls -d $W/w26fix2 2>&1
echo "== envs:"; ls /scratch/jjyeung/envs/
echo "== kit sha"; sha256sum $W/w26fix/n_go/SHA256SUMS.txt $W/w26fix/n_go/b/a.py
ls $W/w26fix/n_go $W/w26fix/n_go/b | head -80
wc -l $T/launch_r1/production_proof.py $T/student_pilot/r1_persisted.py $T/student_pilot/carrier_c1_run.py
echo "==== production_proof.py"; cat -n $T/launch_r1/production_proof.py | head -400
echo "==== r1_persisted.py"; cat -n $T/student_pilot/r1_persisted.py | head -400
echo "==== c1 first_batch_check"; grep -n "def first_batch_check\|^import\|^from" $T/student_pilot/carrier_c1_run.py | head -60
L=$(grep -n "def first_batch_check" $T/student_pilot/carrier_c1_run.py | head -1 | cut -d: -f1); sed -n "${L},$((L+120))p" $T/student_pilot/carrier_c1_run.py
echo "==== z.py seal"; grep -n "def seal" -A25 $W/w26fix/n_go/b/z.py
