#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
[[ -d /scratch/jjyeung/orch_n30/so_cr_corpus ]] || bash $P/cursor_start.sh so_cr_corpus $P/cr_corpus.md
bash $P/poll118o.sh 2>&1 | grep -v "dispatch.*log |" | grep -v "^-- so_\(read\|launch\|git\|cr_step\):"
for t in so_xstore so_pack_a so_step; do echo "== $t: $(tail -c 250 /scratch/jjyeung/orch_n30/$t/work/STATUS.md 2>/dev/null | tr '\n' ' ')"; done
for v in so_cr_launch2 so_cr_read2; do echo "=== $v"; head -c 5000 /scratch/jjyeung/orch_n30/$v/REVIEW_VERDICT.md; echo; done
