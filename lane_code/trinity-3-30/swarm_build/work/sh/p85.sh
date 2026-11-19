R=/scratch/jjyeung/orch_n30
date -u +%TZ; tmux ls -F "#{session_name}" | grep "^sb_" | tr "\n" " "; echo; echo Q: $(cat $R/sb_queue/queue.txt | tr "\n" " "); cat $R/sb_queue/cap
L=$R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log; echo "spend_lines $(wc -l < $L)"; awk -F'|' 'NR>0{s+=$6} END{print "wall_s",s}' $L
for t in sb_ktfix2 sb_phfix sb_cafix sb_rlfix4; do echo "== $t $(head -c 200 $R/$t/STATUS.md 2>/dev/null)"; ls $R/$t/out/*.sha256 2>/dev/null | head -2; done
cat $R/sb_rlfix4/out/sb_rlfix4.tar.sha256 2>/dev/null
