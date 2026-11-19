W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/work/conf21/ff2_focused.log
date -u +%TZ; cat $W/work/conf21/ff2_rc 2>/dev/null; grep -c '\.\.\. ok' $F; grep -E '\.\.\. (ERROR|FAIL)' $F | cut -c1-150 | head -30; grep -n -A12 '^ERROR: ' $F | grep -E 'Error|error|ERROR' | cut -c1-300 | sort | uniq -c | sort -rn | head -15; tail -4 $F
