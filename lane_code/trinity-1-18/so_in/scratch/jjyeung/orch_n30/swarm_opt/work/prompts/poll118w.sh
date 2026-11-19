#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
[[ -d /scratch/jjyeung/orch_n30/so_cr_step2 ]] || bash $P/cursor_start.sh so_cr_step2 $P/cr_step2.md
bash $P/qrun.sh | grep -v "ENDED\|^-- so_\(read\|launch\|git\|cr_step\):"
S=/scratch/jjyeung/orch_n30/so_step; grep -E "^Ran |^OK|^FAILED|EXIT=|SO_GLOO_PROOF" $S/work/review1_full_suite_by_coordinator.txt | cut -c1-300 | tail -5
ls $S/out/kit_timing; for f in $S/out/kit_timing/README* $S/out/kit_timing/*.md; do [[ -f $f ]] && { echo "== $f"; head -c 3000 $f; }; done 2>/dev/null | head -c 4000
grep -n -i "timing kit\|kit_timing" $S/out/REPORT.md | head -8 | cut -c1-300
