T=/scratch/jjyeung/orch_n30/n_review/r1e/tcpp; cd $T; date -u +%TZ
for f in student_pilot/carrier_c1_data.py student_pilot/r1_mix.py student_pilot/r1_population.py student_pilot/r1_loader.py student_pilot/r1_routing.py; do echo "=== $f $(wc -l < $f)"; grep -n -o -E "(row|raw|item|example|r)(\[['\"][a-z_0-9]+['\"]\]|\.get\(['\"][a-z_0-9]+['\"])" $f | awk -F: '{print $2}' | sort | uniq -c | sort -rn | head -40 | tr '\n' ' '; echo; done
grep -n "def \|class " student_pilot/carrier_c1_data.py | head -60
grep -n "class Rows" -A40 student_pilot/carrier_c1_run.py | head -60
