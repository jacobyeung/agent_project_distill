<!-- recovered by seal_plan: transcript=71f94277 line=31824 utc=2026-11-14T14:25:29.827Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ORDER_final_stop_read_first_then_P1_fix.md heredoc_quoted -->
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