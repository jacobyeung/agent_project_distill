#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
bash $P/poll118o.sh 2>&1 | grep -v "dispatch.*log |" | grep -v "^-- so_\(read\|launch\|git\|cr_step\):"
for t in so_xstore so_pack_a; do echo "== $t: $(tail -c 250 /scratch/jjyeung/orch_n30/$t/work/STATUS.md 2>/dev/null | tr '\n' ' ')"; done
echo "== so_step: $(tail -c 250 /scratch/jjyeung/orch_n30/so_step/work/STATUS.md | tr '\n' ' ')"
echo "=== cr_git2 verdict"; cat /scratch/jjyeung/orch_n30/so_cr_git2/REVIEW_VERDICT.md
