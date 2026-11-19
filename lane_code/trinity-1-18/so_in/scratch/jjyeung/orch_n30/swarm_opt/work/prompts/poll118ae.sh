#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
if ! tmux has-session -t =so_modep_fix 2>/dev/null && [[ ! -d /scratch/jjyeung/orch_n30/so_cr_modep2 ]]; then bash $P/cursor_start.sh so_cr_modep2 $P/cr_modep2.md; fi
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
for c in so_cr_git3 so_cr_modep2; do echo "$c: $(head -1 /scratch/jjyeung/orch_n30/$c/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =$c 2>/dev/null && echo y || echo n)"; done
echo "launch gloo: $(grep -E '^Ran|^OK|FAILED|EXIT=' /scratch/jjyeung/orch_n30/so_launch/work/port21_gloo2_by_swarm_opt.txt | tail -3 | tr '\n' ' ') tmux=$(tmux has-session -t =so_launch_gloo 2>/dev/null && echo y || echo n)"
echo "step gloo: $(grep -E '^Ran|^OK|FAILED|EXIT=' /scratch/jjyeung/orch_n30/so_step/work/round2_b21_gloo_by_coordinator.txt | tail -3 | tr '\n' ' ') tmux=$(tmux has-session -t =so_step_gloo3 2>/dev/null && echo y || echo n)"
uptime
