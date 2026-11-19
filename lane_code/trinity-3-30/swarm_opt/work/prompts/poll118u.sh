#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_\(read\|launch\|git\|cr_step\):"
for c in so_cr_corpus so_step_gloo2; do echo "$c tmux=$(tmux has-session -t =$c 2>/dev/null && echo y || echo n)"; done
echo "cr_corpus: $(head -1 /scratch/jjyeung/orch_n30/so_cr_corpus/REVIEW_VERDICT.md 2>/dev/null)"
tail -3 /scratch/jjyeung/orch_n30/so_step/work/review1_full_suite_by_coordinator.txt
for t in so_pack_a so_launch so_modep; do echo "== $t: $(tail -c 200 /scratch/jjyeung/orch_n30/$t/work/STATUS.md 2>/dev/null | tr '\n' ' ')"; done
uptime
