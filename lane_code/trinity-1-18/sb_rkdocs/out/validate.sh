#!/usr/bin/env bash
set -euo pipefail
cd /scratch/jjyeung/orch_n30/sb_rkfix
bash scripts/cpu.sh tests/test_roomkit.py > out/TESTS.log 2>&1
printf '%s\n' 'All CPU tests pass. Final validation is reproducing K1 areas and refreshing input-bound receipts; S1c and R0-dev remain unrun.' > STATUS.md
bash scripts/cpu.sh scripts/reproduce.py > out/S1b.log 2>&1
bash scripts/cpu.sh scripts/summarize_s1.py > out/S1_summary.log 2>&1
bash scripts/cpu.sh scripts/score_room_pricing.py --direct evidence/direct_m200_room134.json --self-test > out/SCORER_SELF_TEST.log 2>&1
bash scripts/cpu.sh scripts/make_go_template.py > out/GO_IDENTITY.txt
bash scripts/cpu.sh out/finalize_delivery.py > out/FINALIZE.log 2>&1
