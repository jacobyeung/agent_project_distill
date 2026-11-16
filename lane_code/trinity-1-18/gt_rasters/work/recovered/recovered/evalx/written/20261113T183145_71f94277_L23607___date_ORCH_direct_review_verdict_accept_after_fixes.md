<!-- recovered by seal_plan: transcript=71f94277 line=23607 utc=2026-11-13T18:31:45.115Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_direct_review_verdict_accept_after_fixes.md heredoc_quoted -->
# ORCH: direct-scope review verdict is ACCEPT AFTER FIXES; the step-1 rehearsal may run as is

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_MILESTONE_DIRECT.md` (31 lines; read it in full). Pins verified (five files; digest b1be1d58 from `sha256(json.dumps(code_pins, sort_keys=True))`). No receipt was written, because the verdict is not ACCEPT. All 43 existing tests pass; the reviewer added three that reproduce F1 to F3: `/scratch/jjyeung/orch_cd/leg_s1_review/work_milestone_direct/milestone/test_review_findings.py` (adopt them).

**The step-1 rehearsal on the direct scope may run now, as reviewed.** None of the findings changes a score.

**Before the step-100 decision read**, each with a test, then re-pin and send me the new digest for a short confirmation pass:

1. **F1 (medium; `chain_save.py:89-96`, `execute_chain.py:143-145`)**: a save that fails on a full disk or is interrupted by a Slurm signal leaves `.save_N.partial`; every later save to that slot fails, so the final failure state is never archived. Make the partial reusable without removing evidence (open it for writing afresh) and prove a later save succeeds. This one matters today: the Orchard project filesystem is nearly full.
2. **F2 (medium; `chain.py:148-166`)**: the authorization names neither the export nor the run and can be used more than once. Require it to carry the spec hash and the output path, single use.
3. **F3 (low to medium; `execute_chain.py:210-215`)**: the final save runs only if an nvidia-smi query succeeds first, and a full output disk at `record()` skips it. Wrap each separately; always attempt the save.
4. **F4 (medium; `execute_chain.py:50-56`)**: the staged code list omits code the chain runs (`legs1_reads/out/direct.py`, `common.py`, `export_check.py`, `BASELINE_CODE_PINS.json`, `camera/report_camera.py`). Add them to the stage's pins.
5. Lower, do them if cheap: F5 (check the producer's done record's content against the artifact, not only its hash), F6 (assert in code that the leg is read with 32 duplicated frames, its training layout), F7 (only the free-space floor, not any save error, should abort a healthy GPU read), F8 (digest independent of absolute paths, so a staged copy does not need a new receipt).

**One gap the reviewer names that I need you to close by reference:** it did not check `legs1_reads/out/decision.py`, the cut by the 47 scenes f17 saw, or the main comparisons against f17 and the parent. Tell me which earlier review covers each (file and verdict line). If the 47-scene cut or any comparison is new code since that review, name the files and I will have them reviewed today.

The routed-scope review is still running.