#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
[[ -d /scratch/jjyeung/orch_n30/so_cr_corpus2 ]] || bash $P/cursor_start.sh so_cr_corpus2 $P/cr_corpus2.md
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
for c in so_cr_corpus2 so_cr_git5 so_cr_read4 so_cr_step4 so_cr_pack_a3; do [[ -d /scratch/jjyeung/orch_n30/$c ]] && echo "$c: $(head -1 /scratch/jjyeung/orch_n30/$c/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =$c 2>/dev/null && echo y || echo n)"; done
for t in so_read so_step so_pack_a so_git so_corpus_fix; do echo "$t: $(head -1 /scratch/jjyeung/orch_n30/$t/out/REPORT.md | cut -c1-160)"; done
uptime; free -g | sed -n 2p
