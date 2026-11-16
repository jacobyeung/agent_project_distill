<!-- recovered by seal_plan: transcript=71f94277 line=32015 utc=2026-11-14T14:46:03.261Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_resubmit_P0_general_2_after_diff_event.md <<'EOF'
# ORCH order: resubmit IF-P0 arm P0 on `general` (second packet), after your diff event

LAUNCH IF-P0 P0 eef3ba96a639d634be9ec9e976ce16aadec648f4eeb07e2bc6fee196d94516bb general a9fa8d8e44ae3c98e

- The canary (169512) reached step 24 with every check passing; if_p0 verified it. This submission is the full run.
- Packet: `/scratch/jjyeung/orch_cd/if_p0/out/P0_SUBMISSION_eef3ba96_general_2/` (token a9fa8d8e44ae3c98e, BATCH.sh sha256 32b564deeae47cf991564e02a5647c78411ec62a506c8a73678da2d6248a4e4b, 12 h). Control files as before: `/scratch/jjyeung/orch_cd/if_p0/out/P0_CONTROL_eef3ba96/`. The first general token (aded62aed7218d81a) is spent; never reuse it.
- When: after you post the diff event for the P1 gate and the report publication, at your next natural break. The gate fix keeps priority because `advanced` is idle and waiting for pilot 4.
- How: the packet's own admission, one test-only call, one real submission, `ALLOW 169526`. It queues behind the final stop read and starts when that ends. No hold, no cancel, no retry. Observe it in your ten-minute batched calls with the same stall rule; only I order a cancel.
- If job 169512 left a terminal return (it was cancelled at about step 24), fetch it with the accepted paced fetch when convenient and put it under if_p0's `inbox_results/aded62aed7218d81a/`; if none exists, say so in STATUS.

One event with the job id.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) if_p0(3) RESULT 1445Z: P0 canary 169512 verified through step 24: selection.json sha 4d53d9b8 (2,667 / 17,478 skips, 9,600 rows), frames 86,396 + 1,664, step-0 equality by control flow, 37.5 s/step (73.6% data/prep) -> 300 steps ~3.1 h, ~3.5 h with staging; no fault. general_2 packet ready (token a9fa8d8e44ae3c98e, sha 32b564de). ORDERED evalx to resubmit P0 on general after its diff event (queues behind final read 169526; ALLOW 169526)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md