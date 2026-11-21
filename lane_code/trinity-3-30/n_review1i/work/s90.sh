W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx; C=$T/student_pilot/carrier_c1_run.py
date -u +%TZ
n=$(grep -n 'def first_batch_check' $C < /dev/null | head -1 | cut -d: -f1); echo "first_batch_check at $n"; sed -n "${n},$((n+150))p" $C < /dev/null | cut -c1-220
echo "== production_proof 1-40"; sed -n 1,40p $T/launch_r1/production_proof.py < /dev/null | cut -c1-220
echo "== bind_prepared tail"; sed -n 210,240p $T/student_pilot/r1_population.py < /dev/null | cut -c1-220
echo "== admit checks"; grep -n "check(\|def finish\|json.dump\|'checks'\|branch_taken\|config_sha256\|tree_sha256\|'identity'" $W/w24z14/out/admit_test.py < /dev/null | cut -c1-200 | head -60
