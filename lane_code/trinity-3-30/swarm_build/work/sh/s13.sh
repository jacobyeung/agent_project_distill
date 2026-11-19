R=/scratch/jjyeung/orch_n30; ls $R/sb_scale2/out | tr "\n" " "; echo; cat $R/sb_scale2/STATUS.md | cut -c1-900
awk -F'|' '{n++; s+=$6} END{print n" jobs "s" s wall"}' $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log
