#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
for c in so_cr_step3 so_cr_pack_a2 so_cr_read3 so_cr_corpus; do echo "$c: $(head -3 /scratch/jjyeung/orch_n30/$c/REVIEW_VERDICT.md 2>/dev/null | tr '\n' ' ' | cut -c1-300) tmux=$(tmux has-session -t =$c 2>/dev/null && echo y || echo n)"; done
echo "git_fix3: $(head -1 /scratch/jjyeung/orch_n30/so_git/out/REPORT.md | cut -c1-200) tmux=$(tmux has-session -t =so_git_fix3 2>/dev/null && echo y || echo n)"
echo "corpus_fix: $(head -1 /scratch/jjyeung/orch_n30/so_corpus_fix/out/REPORT.md 2>/dev/null| cut -c1-200)"
echo "corpus_lost: $(head -1 /scratch/jjyeung/orch_n30/so_corpus_lost/out/REPORT.md 2>/dev/null| cut -c1-200)"
uptime; free -g | head -2
