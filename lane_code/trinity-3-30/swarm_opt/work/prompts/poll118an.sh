#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
bash $P/gloo_step3.sh
f=/scratch/jjyeung/orch_n30/so_step/work/round3_b21_gloo_by_coordinator.txt
echo "step gloo3: $(grep -E '^Ran|^OK|FAILED|EXIT=' $f 2>/dev/null | tail -3 | tr '\n' ' ') proofs=$(grep -c -E 'SO_GLOO_PROOF|SO_ADMISSION_PROOF|SO_FALLBACK_PROOF' $f 2>/dev/null) tmux=$(tmux has-session -t =so_step_gloo3 2>/dev/null && echo y || echo n)"
if grep -q '^EXIT=0' $f 2>/dev/null && [[ ! -d /scratch/jjyeung/orch_n30/so_cr_step4 ]]; then bash $P/cursor_start.sh so_cr_step4 $P/cr_step4.md; fi
bash $P/poll118am.sh
