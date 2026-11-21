T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx; C=$T/student_pilot/carrier_c1_run.py
n=$(grep -n "^def prepared" $C < /dev/null | cut -d: -f1); sed -n "$((n+41)),$((n+75))p" $C < /dev/null
echo "== processor_for"; grep -rn "def processor_for\b\|def processor_for(" $T/student_pilot --include=*.py < /dev/null | head; f=$(grep -rln "def processor_for(" $T/student_pilot --include=*.py < /dev/null | head -1); n=$(grep -n "def processor_for(" $f < /dev/null | cut -d: -f1); sed -n "${n},$((n+25))p" $f < /dev/null
echo "== manifest root writers"; grep -rn "\['root'\]\s*=\|root=str(\|'root':" $T/student_pilot/r1_persisted.py $T/student_pilot/r1_handover.py $C < /dev/null | cut -c1-200 | head -20
