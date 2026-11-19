R=/scratch/jjyeung/orch_n30; cd $R
echo "== cafix proc"; pgrep -af 'agent -p' | cut -c1-200; cat sb_cafix/STATUS.md | cut -c1-300; cat sb_cafix/cursor.log; tail -20 sb_cafix/out/v2/STATUS_LOG.md | cut -c1-300
echo "== ktfix2"; ls -la --time-style=+%H:%M sb_ktfix2 sb_ktfix2/out 2>&1 | head -40; ls $R/codex_local/agent/scratch/codex_runs/ | grep ktfix2; d=$(ls -d $R/codex_local/agent/scratch/codex_runs/*ktfix2* 2>/dev/null | tail -1); ls -la $d; tail -c 3000 $d/*last* 2>/dev/null; tail -c 2000 $d/stderr* 2>/dev/null
echo "== phrase reg"; P=sb_mask_phrase; for f in PROMPT.md in/KIT_SPEC_mask_phrase.md in/v2/KIT_SPEC_mask_phrase.md; do sha256sum $P/$f; stat -c '%y' $P/$f; done
grep -n -i -E 'bar|1\.5|-1\.0|lower bound|W1|W2|W_cf|parity' $P/PROMPT.md | head -40 | cut -c1-400
echo "-- first spec"; grep -n -i -E '1\.5|-1\.0|lower bound|parity|W_cf|Bars' $P/in/KIT_SPEC_mask_phrase.md | head -20 | cut -c1-400
ls -la --time-style=+%FT%T.%N $P/work/caps | sort -k6 | head -3
ls $P/work/orig_out 2>/dev/null | head; ls sb_phfix/sb_mask_phrase/out/ 2>/dev/null | head -20
