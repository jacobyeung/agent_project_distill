W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; R=$W/w21/out/BUILD21_REPORT.md; B=$W/w21/work/build21
head -c 9000 $R; echo; echo ---FT; grep -n 'final_focused\|B21_PROOF\|subprocess\|run.sh' $B/final_tools21.py | head -20; ls $B | sed -n '50,200p' | tr '\n' ' '
