<!-- recovered by seal_plan: transcript=71f94277 line=30381 utc=2026-11-14T09:27:42.963Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ORDER_native_pilot_2_launch.md heredoc_quoted -->
# ORCH: family de98ac22 confirmed by my diff read; launch the second native pilot

I read the 217-line diff (`packages_s23/RUNTIME.patch`): the export destination guard, the generation-pinned header listing before the fetch, and the inventory reconciliation after extraction. Accepted on top of the two independent reviews.

Gate records for token e495c2771:
- `/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PILOT_CONTROL_e495c2771/REVIEW.json`
- `/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PILOT_CONTROL_e495c2771/ORDER.md` (one line `LAUNCH EVALX NATIVE pilot 200 general e495c2771 <family> <artifact>`)

Do: prepare the real packet; CPU admission and batch validation; the Orchard connection is restored (see my clearance note), so first one observation of jobs 169491 and 169493; then the queue and main-notice check with `ALLOW 169491 169493`; test-only; one real submission; RESULT with the job id and the three jobs' states. Report the pilot's measurements as ordered at 0815Z. No further pilot without my word.