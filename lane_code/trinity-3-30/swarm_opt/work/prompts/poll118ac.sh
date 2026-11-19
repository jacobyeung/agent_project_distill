#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
[[ -d /scratch/jjyeung/orch_n30/so_cr_git3 ]] || bash $P/cursor_start.sh so_cr_git3 $P/cr_git3.md
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
for c in so_cr_git3; do echo "$c: $(head -1 /scratch/jjyeung/orch_n30/$c/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =$c 2>/dev/null && echo y || echo n)"; done
echo "launch gloo: $(grep -E '^Ran|^OK|FAILED|EXIT=' /scratch/jjyeung/orch_n30/so_launch/work/port21_gloo_by_swarm_opt.txt | tail -3 | tr '\n' ' ')"
for t in so_step so_modep so_corpus_fix so_corpus_lost so_pack_a; do echo "== $t: $(head -1 /scratch/jjyeung/orch_n30/$t/out/REPORT.md 2>/dev/null | cut -c1-250)"; done
uptime
