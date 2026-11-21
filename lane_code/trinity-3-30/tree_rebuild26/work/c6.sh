K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n_go; cd $K/b
grep -n "q\.steps\|WAITING_REVIEW\|'v\.json'\|\"v\.json\"\|q\.log\|f1\.json\|'live'\|\"live\"\|/o/\|'o'" *.py *.sh 2>/dev/null | cut -c1-220 | head -60
echo ---pc.sh; cat pc.sh | head -60
