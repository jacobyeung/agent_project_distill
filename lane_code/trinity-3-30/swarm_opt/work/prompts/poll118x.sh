#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "^-- so_\(read\|launch\|git\|cr_step\):" | grep -v "so_\(read\|launch\|git\)_fix ENDED"
echo "cr_step2: $(head -1 /scratch/jjyeung/orch_n30/so_cr_step2/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =so_cr_step2 2>/dev/null && echo y || echo n)"
echo "=== pack_a REPORT"; head -c 2500 /scratch/jjyeung/orch_n30/so_pack_a/out/REPORT.md; echo; ls /scratch/jjyeung/orch_n30/so_pack_a/out
for t in so_modep so_read so_git; do echo "== $t: $(tail -c 200 /scratch/jjyeung/orch_n30/$t/work/STATUS.md 2>/dev/null | tr '\n' ' ')"; done
uptime
