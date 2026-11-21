T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
n=$(grep -n "def pinned" $T/student_pilot/p3_provenance.py < /dev/null | cut -d: -f1); sed -n "$((n-3)),$((n+25))p" $T/student_pilot/p3_provenance.py < /dev/null
echo "== r1_persisted 1-70"; sed -n 1,70p $T/student_pilot/r1_persisted.py < /dev/null
echo "== hooks"; grep -rn "p3_provenance\.\w* *=\|provenance\.\w* *= \|_resolver\|RESOLVE" $T/student_pilot $T/launch_r1 --include=*.py < /dev/null | cut -c1-200 | head -20
