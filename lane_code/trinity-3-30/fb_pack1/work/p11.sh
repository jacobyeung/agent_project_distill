W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w24/work/tree_r1/student_pilot
date -u +%FT%TZ; ls $W/w24/work/tree_r1 | tr '\n' ' '; echo
sed -n 1,95p $T/r2_exclusions.py; echo ====INTAKE; sed -n 25,75p $T/r2_intake.py
echo ==sources; grep -n "source_names\|SLICE_CELLS\|camera" $T/r1_coverage.py | head -20
