R=/scratch/jjyeung/orch_n30
date -u +%TZ; free -g | sed -n 2p; df -h /scratch | tail -1; tmux ls 2>/dev/null | cut -d: -f1 | tr "\n" " "; echo
echo "== queue"; tail -6 $R/sb_queue/codexq.log; cat $R/sb_queue/queue.txt | tr "\n" " "; echo
echo "== running codex"; pgrep -af "codex" | grep -o "label [a-zA-Z0-9_]*" | sort | uniq -c
echo "== latest runs"; ls -t $R/codex_local/agent/scratch/codex_runs/ | head -14
echo "== spend"; wc -l < $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log; tail -5 $R/codex_local/agent/scratch/codex_runs/CODEX_SPEND.log
for t in sb_fpjoin sb_rowD4 sb_rowA2 sb_rowB3 sb_rowOI sb_rowLR sb_auditfix sb_roomkit; do d=$(ls -d $R/codex_local/agent/scratch/codex_runs/*_$t 2>/dev/null | tail -1); echo "== $t $d"; ls $d 2>/dev/null | tr "\n" " "; echo; [ -f $d/final_message.md ] && head -c 700 $d/final_message.md; echo; done
for c in sb_recrev sb_f64; do echo "== cursor $c"; ls -t $R/$c | head -5 | tr "\n" " "; echo; tail -c 500 $R/$c/cursor.log 2>/dev/null; echo; done
echo "== rows_r1 mirror"; ls /scratch/jjyeung/n30_mirror/ 2>/dev/null | tr "\n" " "; ls /scratch/jjyeung/n30_mirror/rows_r1 2>/dev/null | head
