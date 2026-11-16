<!-- recovered by seal_plan: transcript=71f94277 line=31824 utc=2026-11-14T14:25:29.827Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_final_stop_read_first_then_P1_fix.md <<'EOF'
# ORCH order: tie cap answered; final stop read first; P0 gives up the `general` slot

## 1. Tie cap (your 1423Z question)

My text contradicted my test. The cap is **max(1, checked // 100)**: one tie in 126 positions passes, two fail. The rest of the rule stands (same top-2 id set, both margins at most 1.0, sequence exact, cached positions complete).

## 2. Final stop read, now, before the P1 fix

The trainer exited at 14:04:31Z; the final step is **544**. The operator delivered the attested stop export to your inbox (artifact 1d6eeb28..., attestation dc3d7d44..., sidecar 217f9616..., archive `q8/8865619b/469ddece_mstop.tar`, 21,583,032,320 B; delivery proof `/scratch/jjyeung/orch_cd/orchard_cp2/out/EXPORT_STOP_DELIVERY_169097_m544.json`). This is the pre-authorized final stop read: stop route, bindings `stop_bound_s22/BINDING.json`, launcher digest 4bbcd73f, reader b8ebab38, one submission on `general`, no retry. Its packet carries the same contents as the step-400 packet, with the budget-hit comparison leaving out object_abs_distance and room_size_estimation, and the per-archive size override rule already given.

## 3. P0 169512 yields the slot

The final read outranks the IF-P0 canary, and its launcher admits only `general`. In the same batched call that submits the final stop read, first capture P0's live evidence (phases reached, any step records and their times, the job log tail), then run exactly `scancel 169512`, once. Read back both jobs' states. Deliver P0's captured evidence to if_p0's inbox with one line. If the stop read's admission fails, do not cancel P0; tell me.

## 4. Then the P1 gate fix

As ordered at 14:20Z, with the cap above. Pilot 4 and the full routed read are planned for `advanced`, which frees when the production job reaches a terminal state (the operator will tell me). Build pilot-4 packets for both partitions.

One event when the final read is submitted and P0 is cancelled (job id, states). One event with the P1 diff.
EOF
cat > /scratch/jjyeung/orch_cd/if_p0/inbox/${N}_ORCH_NOTE_P0_canary_yields_slot_build_new_general_packet.md <<'EOF'
# ORCH note: the P0 canary (169512) passed all staging and will be cancelled for the final evaluation read; build a fresh `general` packet

- Job 169512 (seal eef3ba96) started at 14:01:05Z. By 14:14:43Z it had passed every staging phase including the frame copies (`pose_frames_copied`, six held-out copies), which no earlier job had reached, and the runtime check. The load guard did not refuse. Whether `prepare`, the step-0 check and training steps were reached before the cancel will be in the evidence evalx delivers to your inbox.
- The production run ended (step 544) and its final evaluation read needs our one `general` slot, so I ordered evalx to cancel 169512 when it submits that read. This is a slot decision, not a fault of the job.
- Build now, build-only, a fresh `general` packet at seal eef3ba96 (new token; the first one is spent), in `out/P0_SUBMISSION_eef3ba96_general_2/`, validated as before. P0 will be resubmitted on `general` when the final read finishes (about 16:00Z) or on `advanced` (token a4d4bf68ec3f6615f) if that frees first; I decide then.
- When evalx's evidence arrives, post the canary RESULT your brief asks for with whatever was reached. If the evidence shows a failure in `prepare` or later, fix and reseal at once.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) Orders: evalx (inbox ${N}_ORCH_ORDER_final_stop_read_first_then_P1_fix.md): tie cap = max(1, checked//100); FINAL STOP READ (step 544, stop route) first, one submission on general; capture P0 169512's evidence then scancel it in the same call; then the P1 gate fix and pilot-4 packets for both partitions. if_p0: build a fresh general packet (eef3ba96) for a resubmission after the final read. P0 169512 had passed all staging incl. frame copies by 14:14Z." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md