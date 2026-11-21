T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ
echo "== ContextVar in tree"; grep -rn "ContextVar(" $T/student_pilot $T/launch_r1 --include=*.py < /dev/null | cut -c1-200
echo "== processor_for_receipt"; n=$(grep -n "def processor_for_receipt" $T/student_pilot/carrier_c1_run.py < /dev/null | cut -d: -f1); sed -n "${n},$((n+30))p" $T/student_pilot/carrier_c1_run.py < /dev/null
echo "== def prepared"; n=$(grep -n "^def prepared" $T/student_pilot/carrier_c1_run.py < /dev/null | cut -d: -f1); sed -n "${n},$((n+40))p" $T/student_pilot/carrier_c1_run.py < /dev/null
