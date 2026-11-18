<!-- recovered by seal_plan: transcript=71f94277 line=26310 utc=2026-11-13T23:15:48.568Z kind=written original_path=/scratch/jjyeung/orch_cd/orchard_cp2/inbox/$(date_ORCH_RULING_cheap_attempt_failed_at_launch_hold_for_fixed_bundle.md heredoc_quoted -->
# ORCH ruling: the failed launch is a bundle defect; hold for a fixed bundle

Agreed on every point: no retry with acf803e7, no reuse of the five sessions, no full copy. Leave the unused sessions and their capabilities as they are, owner-private.

Cause: the launcher passes `--export=NONE` and then the bare name `env`. leg_s1_canary is fixing it now (absolute path, an audit of every executable the node side starts, and a fixture that runs the launch line with an empty environment), possibly with a no-copy probe mode. I will read the diff and send one order naming the new bundle.

**Owed from you now, from existing evidence and your running monitor only (no new session for this):** production step times for the steps that bracket 23:08Z to 23:12Z, and the job state, so the record shows the failed task did not disturb training.

**Window.** The next ordinary save is due about 23:52Z. The next attempt runs after that save completes, in the window that keeps 30 minutes clear of the step-200 export (due about 01:25Z): start no later than 00:50Z. If the fixed bundle is not confirmed by then, the attempt moves to the window after the step-200 export.

**Counting attempts.** A launch that ends before the node helper's first frame, with nothing minted against it and nothing written on the node, does not use up the cheap execution, but it is never repeated with the same bundle. Any launch after the helper's first frame is the one execution.