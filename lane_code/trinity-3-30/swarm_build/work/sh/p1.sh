R=/scratch/jjyeung/orch_n30; cd $R
date -u; free -g | head -2; df -h /scratch | tail -1
tmux ls 2>&1 | grep -E 'sb_|cursor' 
echo "== cafix"; ls -la --time-style=+%H:%M sb_cafix sb_cafix/out sb_cafix/out/v2 2>&1 | head -40; tail -c 1500 sb_cafix/cursor.log 2>/dev/null
echo "== ktfix2"; sed -n 1,80p sb_ktfix2/out/FIX2_REPORT.md 2>&1 | cut -c1-400
echo "== phfix"; sed -n 1,40p sb_phfix/out/PHFIX_NOTES.md | cut -c1-400
echo "== rlfix4"; sed -n 1,50p sb_rlfix4/out/FIX4_REPORT.md | cut -c1-400
echo "== phrase bars"; ls -la --time-style=+%FT%T sb_mask_phrase/out | head -40; find sb_mask_phrase -name 'BARS*.json' -o -name 'PER_ITEM*' | head; for f in $(find sb_mask_phrase -name 'BARS*.json'); do echo "--$f"; sha256sum $f; stat -c '%y' $f; cat $f | head -c 3000; done
echo "== spend"; S=$R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log; wc -l $S; tail -3 $S
