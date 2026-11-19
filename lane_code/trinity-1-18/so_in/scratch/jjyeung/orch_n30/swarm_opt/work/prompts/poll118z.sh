#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
tmux has-session -t =so_realgit3 2>/dev/null || [[ -d /scratch/jjyeung/orch_n30/so_git/work/realgit3_by_swarm_opt ]] || { tmux new-session -d -s so_realgit3 "bash $P/realgit2.sh > /scratch/jjyeung/orch_n30/so_git/work/realgit3_launch.txt 2>&1"; echo started realgit3; }
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
for c in so_cr_modep so_cr_pack_a so_cr_step2; do echo "$c: $(head -1 /scratch/jjyeung/orch_n30/$c/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =$c 2>/dev/null && echo y || echo n)"; done
cat /scratch/jjyeung/orch_n30/so_git/work/realgit3_launch.txt 2>/dev/null | tail -12
uptime
echo "=== launch gloo cmd"; grep -n -i -B2 -A12 "gloo" /scratch/jjyeung/orch_n30/so_launch/out/REPORT.md | grep -i -A10 "command\|\`\`\`" | head -30 | cut -c1-300
