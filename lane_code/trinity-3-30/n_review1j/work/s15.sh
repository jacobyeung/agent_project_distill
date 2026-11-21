C=/scratch/jjyeung/orch_n30/n_review/r1j/t/student_pilot; F=$C/s1_exclusions.py
grep -n "^def \|^class \|    def " $F < /dev/null
n=$(grep -n "^def selection" $F < /dev/null | cut -d: -f1); sed -n "${n},$((n+50))p" $F < /dev/null
F2=$C/r2_scene_bindings.py; sed -n 45,66p $F2 < /dev/null
