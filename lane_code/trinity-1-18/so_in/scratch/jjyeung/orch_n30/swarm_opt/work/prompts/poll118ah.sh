#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
for c in so_cr_pack_a2:cr_pack_a2.md so_cr_read3:cr_read3.md; do n=${c%%:*}; [[ -d /scratch/jjyeung/orch_n30/$n ]] || bash $P/cursor_start.sh $n $P/${c##*:}; done
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
for c in so_cr_step3 so_cr_pack_a2 so_cr_read3; do echo "$c: $(head -1 /scratch/jjyeung/orch_n30/$c/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =$c 2>/dev/null && echo y || echo n)"; done
echo "git_fix3: $(head -1 /scratch/jjyeung/orch_n30/so_git/out/REPORT.md | cut -c1-200)"
uptime
