date -u
for t in filter move; do W=/scratch/jjyeung/orch_n30/sm_cr_$t; echo "== $t"; tail -c 300 $W/cursor.log; echo; ls $W; head -c 6000 $W/REVIEW_VERDICT.md 2>/dev/null; done
