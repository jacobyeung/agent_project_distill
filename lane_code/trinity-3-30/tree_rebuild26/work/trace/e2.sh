set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; T=$W/w26fix/tree
echo "== build24k rest"; ls $W/w24/work/build24k | tail -n +60
echo "== K6 report"; head -c 6000 $W/w24/work/build24k/REHEARSAL_K6_REPORT.md
echo; echo "== python grep in K reports"; grep -h -o '/scratch/[^ "`]*python[0-9.]*' $W/w24/work/build24k/*.md 2>/dev/null | sort | uniq -c | head
echo "== pp wc"; wc -l $T/launch_r1/production_proof.py $T/student_pilot/s1_admission.py $T/student_pilot/rehearsal.py 2>&1
echo "== pp"; cat $T/launch_r1/production_proof.py | head -260
echo "== s1 imports"; grep -n '^\s*\(import\|from\) ' $T/student_pilot/s1_admission.py | head -80
echo "== admit def"; grep -n 'def admit\|prepare_only\|cuda\|device_count\|is_available' $T/student_pilot/s1_admission.py | head -60
echo "== rehearsal"; head -80 $T/student_pilot/rehearsal.py
echo "== q0"; ls $T/launch_s1 2>&1 | head; ls $W/w26fix/src $W/w26fix/pk 2>&1 | head -30
echo "== z11b"; ls $W/w24z11b/work/build24m4z11b | head -60
