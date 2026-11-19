W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; R=$W/w21/out/BUILD21_REPORT.md; B=$W/w21/work/build21
grep -n -v '^|' $R | awk -F: 'length($0)<300 && length($0)>5' | head -80
echo ---FF; head -30 $B/final_focused.log; tail -5 $B/final_focused.log; grep -n 'final_focused' $B/*.py | head -8
