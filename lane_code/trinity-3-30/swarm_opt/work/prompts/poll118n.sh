#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
if ! tmux has-session -t =so_read_fix 2>/dev/null && [[ ! -d /scratch/jjyeung/orch_n30/so_cr_read2 ]]; then bash $P/cursor_start.sh so_cr_read2 $P/cr_read2.md; fi
bash $P/poll118m.sh
for c in so_cr_read2 so_cr_pack2; do W=/scratch/jjyeung/orch_n30/$c; [[ -d $W ]] && echo "-- $c: verdict=$(head -1 $W/REVIEW_VERDICT.md 2>/dev/null) running=$(tmux has-session -t "=$c" 2>/dev/null && echo y || echo n)"; done
