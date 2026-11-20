cd /scratch/jjyeung/orch_n30/tree_rebuild15_w24l/work
ls -la --time-style=+%FT%T tree_r1*/student_pilot/s1_exclusions.py | head; 
P=tree_r1_24l4s/student_pilot
wc -c $P/s1_exclusions.py $P/r2_exclusions.py $P/r0_exclusion.py $P/r2_withheld.py $P/r2_withheld.json
echo ===== s1; cat $P/s1_exclusions.py
echo ===== r2; cat $P/r2_exclusions.py
echo ===== r0; cat $P/r0_exclusion.py
