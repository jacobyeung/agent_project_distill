<!-- recovered by seal_plan: transcript=71f94277 line=32196 utc=2026-11-14T15:12:20.781Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/leg_s1_canary/inbox/${N}_ORCH_TASK_build_real_slot_cpu_check_packet.md <<'EOF'
# ORCH task: build the real-slot CPU check and the baseline capture as ready packets, build-only

Your 15:10Z statement is clear: before any second GPU allocation, slot A (step 544) needs the real CPU restore-and-compare check, and the loss baseline must be captured from the authenticated mirror. The user has not decided on a continuation, so nothing is submitted. Make both steps ready so that a yes costs no preparation time:

1. Build the real-slot CPU check packet for slot A (the original 112,988,477,440-byte archive, manifest 0450e3a3..., kit 07ca49df) with the operator, who holds the Orchard-side records and submits production-side jobs. State in one RESULT: the exact submission command; partition (the entry requests `general`; say whether `advanced` would admit this zero-GPU job, from the operator's knowledge of the limits, without any Orchard call); CPUs, memory, wall limit; the private free space it needs and where; your best estimate of its duration and peak memory with the reasoning (the fixture's 756 tensor comparisons scaled to the real state, restore time measured in production); what PASS and FAIL look like and what each would mean for the continuation.
2. Build the baseline capture step (the last 5 to 20 complete steps ending at 544, prefer 525 to 544, from the authenticated mirror) as a second small packet that runs after a PASS: its command, its read bounds, its output.
3. Say which of the two could run in one job to save a queue wait, and whether either touches anything a running evaluation job uses.
4. No Orchard call, no job. Exchange files with the operator through inbox notes. One RESULT when both packets are ready or blocked.
EOF
cat > /scratch/jjyeung/orch_cd/orchard_cp2/inbox/${N}_ORCH_NOTE_canary_cpu_check_packet.md <<'EOF'
# ORCH note: the canary lane is building the real-slot CPU check and the baseline capture, build-only

Its task: `/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/` (file name containing `build_real_slot_cpu_check_packet`). Give it what it asks for from your records (slot A's metadata, the terminal reconciliation, the limits of `general` and `advanced` for a zero-GPU job, restore times). This is part of your continuation packet's gate list; fold its answer into your CONTINUATION_READY result. Still no submission of anything: the user has not decided.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) canary RESULT 1510Z (continuation readiness): canary3 FAIL = an unmet two-update contract, no measured tensor difference; before any second GPU allocation the checker needs a real-slot CPU restore-and-compare job (general, 16 CPUs, 800G, 0 GPUs, <=5 h, 554 GB private space; duration unmeasured) and a loss baseline captured from the authenticated mirror (steps 525-544) after PASS. Ordered canary + operator to build both as ready packets, build-only (no submission; user undecided)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md