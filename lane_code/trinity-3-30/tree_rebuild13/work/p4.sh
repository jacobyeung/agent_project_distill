T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1; cd $T
grep -rn "SLICE_CELLS\|routing_inputs\|compose_native\|row_sources'\]" --include=*.py . | grep -v "/tests/" | cut -c1-220 | head -40
echo; grep -n "SLICE_CELLS *=" -A6 student_pilot/r1_population.py | head
echo; ls /scratch/jjyeung/orch_n30/tree_rebuild10_w/w22/work/build22 2>/dev/null | head -30 | tr '\n' ' '
echo; sed -n 1,60p /scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build22.md | cut -c1-400
