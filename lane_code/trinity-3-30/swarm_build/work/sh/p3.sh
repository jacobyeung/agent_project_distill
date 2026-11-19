R=/scratch/jjyeung/orch_n30; cd $R
cat sb_ktfix2/STATUS.md; cat $R/codex_local/agent/scratch/codex_runs/20261119T111229Z_sb_ktfix2/meta.json; echo; tail -c 4000 $R/codex_local/agent/scratch/codex_runs/20261119T111229Z_sb_ktfix2/transcript.log
ls -la --time-style=+%H:%M sb_ktfix2/out/ | tail -12; ls sb_ktfix2/work | head
stat -c '%y %n' sb_cafix/STATUS.md sb_cafix/out/v2/* | sort | tail -3
