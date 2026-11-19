T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1; cd $T
echo "## production_proof 55-95"; sed -n 55,95p launch_r1/production_proof.py
echo "## entry 140-185"; sed -n 140,185p launch_r1/entry.py
echo "## source_names"; grep -n "def source_names" -A25 student_pilot/r1_coverage.py | head -40
echo "## compose_native"; grep -n "def compose_native" -A45 student_pilot/r1_routing.py | head -60
