T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx; C=$T/student_pilot/carrier_c1_run.py
n=$(grep -n "^def prepared" $C < /dev/null | cut -d: -f1); m=$(awk -v s=$n 'NR>s && /^def /{print NR; exit}' $C); sed -n "$((m-25)),$((m-1))p" $C < /dev/null
echo "== model_manifest"; grep -rn "def model_manifest\|def manifest_for\|def load_manifest" $T/student_pilot --include=*.py < /dev/null | head
