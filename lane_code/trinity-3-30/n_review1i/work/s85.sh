W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ
echo "== production_proof.py 120-200"; sed -n 120,200p $T/launch_r1/production_proof.py < /dev/null | cut -c1-250
echo "== r1_population.py 120-210"; sed -n 120,210p $T/student_pilot/r1_population.py < /dev/null | cut -c1-250
for f in $W/w24z8b/out/j7.py $W/w24z12/out/j7.py $W/w24z15/out/j8.py; do [ -f $f ] && { echo "== $f"; sha256sum $f < /dev/null; head -c 4000 $f < /dev/null; echo; }; done
ls $W/w24z16b/out $W/w24z16/out < /dev/null 2>&1 | head -20
