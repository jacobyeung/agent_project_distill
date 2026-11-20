T=/scratch/jjyeung/orch_n30/n_review/r1e/tcpp; cd $T || exit 1
sed -n 355,380p student_pilot/carrier_c1_run.py; echo ----; grep -n "def \|route_decision\|_routed(\|is_route" student_pilot/carrier_c1_run.py | grep -n "" | awk -F: '$2>340 && $2<400' ; grep -n "$(sed -n 360,375p student_pilot/carrier_c1_run.py | grep -o 'def [a-z_0-9]*' | head -2 | sed 's/def //' | paste -sd'|')" -r --include=*.py student_pilot launch_r1 | head -20
echo ----; sed -n 25,50p student_pilot/r1_population.py; echo ----; sed -n 95,115p student_pilot/r2_mix.py
