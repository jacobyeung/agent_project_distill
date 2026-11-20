T=/scratch/jjyeung/orch_n30/n_review/r1e/tcpp; cd $T
grep -n "^def \|^class " student_pilot/carrier_c1_routing.py | head -60
for fn in encode tool_mode; do L=$(grep -n "^def $fn(" student_pilot/carrier_c1_routing.py | cut -d: -f1); echo "=== $fn @ $L"; sed -n "${L},$((L+45))p" student_pilot/carrier_c1_routing.py; done
sed -n 185,205p student_pilot/carrier_c1_routing.py
