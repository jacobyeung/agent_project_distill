export TZ=UTC; date -u +%TZ; X=/project/community/jjyeung/okh7/x_22c714e1
squeue -u $USER -o "%.10i %.10P %.24j %.8T %.10M %R"
for J in 173555 173556; do test -f $X/j/a15_cot_ap24d9b8e2_$J.log && { echo "== $J"; grep -v "archive members verified\|staged$\|joined" $X/j/a15_cot_ap24d9b8e2_$J.log | tail -6 | cut -c1-250; }; done
sacct -u $USER -S 2026-11-19T23:40 -E 2026-11-19T23:57 -X -o JobID,Partition,State,Start,End,NodeList%22 -n | grep community-2
