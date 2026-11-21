R=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs
for d in $R/20261121T012809Z_lever3_r4pil $R/20261121T013809Z_lever3_r4pilrev $R/20261121T013250Z_lever3_r1e80 $(ls -d $R/*lever3_r1e80rev 2>/dev/null); do echo "== $(basename $d)"; head -c 2600 $d/final_message.md 2>/dev/null || echo "(running)"; echo; done
