#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
for c in so_cr_modep2 so_cr_step3; do echo "$c: $(head -1 /scratch/jjyeung/orch_n30/$c/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =$c 2>/dev/null && echo y || echo n)"; done
f=/scratch/jjyeung/orch_n30/so_launch/work/port21_gloo3_by_swarm_opt.txt; echo "launch gloo: $(grep -E '^Ran|^OK|FAILED|EXIT=' $f | tail -3 | tr '\n' ' ') tmux=$(tmux has-session -t =so_launch_gloo 2>/dev/null && echo y || echo n)"; grep -E "^(ERROR|FAIL):" $f | sed "s/(.*//" | head -12; grep -E "^[A-Za-z]*Error" $f | sort | uniq -c | sort -rn | head -4 | cut -c1-200
echo "pack_a: $(head -1 /scratch/jjyeung/orch_n30/so_pack_a/out/REPORT.md | cut -c1-250)"
uptime
