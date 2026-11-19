R=/scratch/jjyeung/orch_n30; ls $R/sb_scale2/out 2>/dev/null | tr "\n" " "; echo; cat $R/sb_scale2/STATUS.md 2>/dev/null | cut -c1-900; ps -eo etime,args | grep "[c]odex exec" | grep -c sb_scale2
awk '{n++} END{print n" lines"}' $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log; tail -2 $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log | cut -c1-300
