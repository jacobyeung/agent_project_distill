T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/tree_r1
awk 'NR<=91 && /^def /{d=$0} NR==90{print "r1_rooms:90 in", d}' $T/student_pilot/r1_rooms.py
awk 'NR<=21 && /^def /{d=$0} NR==20{print "r1_routing:20 in", d}' $T/student_pilot/r1_routing.py
awk 'NR<=177 && /^def /{d=$0} NR==176{print "r1_coverage:176 in", d}' $T/student_pilot/r1_coverage.py
grep -n "def verify_audit" $T/student_pilot/r1_rooms.py
grep -n -E "^(def|    def) " $T/student_pilot/r1_launch22.py | head; sed -n 20,60p $T/student_pilot/r1_launch22.py
