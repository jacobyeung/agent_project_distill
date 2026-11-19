R=/scratch/jjyeung/orch_n30; W=$R/tree_rebuild10_w
date -u +%FT%TZ
sed -n 1,25p $R/sb_rowC/out/REPORT.md | cut -c1-400; echo ==GC; cat $R/sb_rowC/out/GRAMMAR_CONFLICT.md | cut -c1-400
echo ==C3; sed -n 1,12p $R/sb_rowC3/out/REPORT.md | cut -c1-400
head -c 1500 $R/sb_rowC3/out/sb_rowC3.jsonl; echo
ls $W/work | tr '\n' ' '; echo; ls $W/w24/work | tr '\n' ' '; echo
T=$(ls -d $W/work/conf24c/pkg 2>/dev/null); echo T=$T; ls $T | head
sed -n 1,90p $T/student_pilot/r2_exclusions.py
