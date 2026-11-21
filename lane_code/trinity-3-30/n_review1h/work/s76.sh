W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx; R=$W/w24/work/build24k/rehearsal_k6
date -u +%TZ
echo "== r1_population.py 90-215"; sed -n 90,215p $T/student_pilot/r1_population.py < /dev/null | cut -c1-260
echo "== carrier first_batch_check 3088-3230"; sed -n 3088,3230p $T/student_pilot/carrier_c1_run.py < /dev/null | cut -c1-260
echo "== cs.py 76-130"; sed -n 76,130p $K/b/cs.py < /dev/null | cut -c1-260
echo "== production_proof.py 1-60"; sed -n 1,60p $T/launch_r1/production_proof.py < /dev/null | cut -c1-260
echo "== routing_types.json 173881"; cat $W/work/d173881/173881/routing_types.json < /dev/null
echo "== rehearsal p"; ls $R/p $R/p/q $R/p/q/b $R/p2 < /dev/null 2>&1 | head -60
