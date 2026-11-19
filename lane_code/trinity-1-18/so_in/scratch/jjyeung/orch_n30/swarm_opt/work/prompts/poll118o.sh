#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
date -u +%H:%M:%SZ
if tmux has-session -t =so_pack_fix 2>/dev/null; then tmux kill-session -t =so_pack_fix && echo "stopped so_pack_fix (Sol) $(date -u +%H:%M:%SZ)"; fi
for f in /scratch/jjyeung/orch_n30/so_*/work/dispatch*.log; do echo "$f | $(grep -m1 -o -i 'model[^,;]\{0,40\}' $f | head -1) | $(stat -c %y $f | cut -c1-16)"; done 2>/dev/null
bash $P/qrun.sh
for c in so_cr_git2:cr_git2.md so_cr_launch2:cr_launch2.md; do n=${c%%:*}; [[ -d /scratch/jjyeung/orch_n30/$n ]] || bash $P/cursor_start.sh $n $P/${c##*:}; done
if ! tmux has-session -t =so_read_fix 2>/dev/null && [[ ! -d /scratch/jjyeung/orch_n30/so_cr_read2 ]]; then bash $P/cursor_start.sh so_cr_read2 $P/cr_read2.md; fi
for c in so_cr_git2 so_cr_launch2 so_cr_read2; do W=/scratch/jjyeung/orch_n30/$c; [[ -d $W ]] && echo "-- $c: verdict=$(head -1 $W/REVIEW_VERDICT.md 2>/dev/null) running=$(tmux has-session -t "=$c" 2>/dev/null && echo y || echo n)"; done
uptime
