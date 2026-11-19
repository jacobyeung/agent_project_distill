R=/scratch/jjyeung/orch_n30
head -c 3000 $R/sb_rowD2/out/MISSING.json; echo; grep -n -i -E "missing|refus" $R/sb_rowB2/out/REPORT.md | head -12
