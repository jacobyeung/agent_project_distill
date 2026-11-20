T=/scratch/jjyeung/orch_n30/n_review/r1e/tcpp; cd $T
sed -n 433,466p student_pilot/carrier_c1_data.py; echo ====; sed -n 511,555p student_pilot/carrier_c1_routing.py
echo ==== checks; for f in row_text_audit r1_training extent_receipt r1_coverage r0_exclusion r2_contract; do echo "--- $f"; grep -n -o -E "(row|value|raw)(\[['\"][a-z_0-9]+['\"]\]|\.get\(['\"][a-z_0-9]+['\"])" student_pilot/$f.py | awk -F: '{print $2}' | sort | uniq -c | tr '\n' ' '; echo; done
grep -n "def row_check" -A25 student_pilot/r1_training.py | head -30
grep -n "def check" -A20 student_pilot/row_text_audit.py | head -40
