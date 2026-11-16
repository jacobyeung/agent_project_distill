<!-- recovered by seal_plan: transcript=a97ad692 line=462 utc=2026-11-15T04:54:06.875Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_ORDER_pilot9_review_verdict_R1_R3.md heredoc_quoted -->
# ORCH ORDER: independent verdict on pilot 9 is SUBMIT WITH NOTED RISKS; two checks before you seal

Verdict (Claude Opus, read-only): `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_PILOT9_COVERAGE.md`. It confirms the seven stand-ins against the real call sites, all 44 code.tar members against `sources/`, and every pin of worker 079f876a and code object 4d05c37b. Read its R1 to R5; two need an answer from you before the seal.

**R1.** A `ProgramRefusal` in any served pair becomes a `refusal_decode` record without `decode_budget` (`nomdg.py:479-480`); `native_metrics.py:257-263` then reads `sampled == 0` and raises at `native_worker.py:276` after all ten pairs, and `native_job.terminal` (native_job.py:155) raises the same error.
**R3.** The 2,400 s limit counts from process start, and geometry now runs over all 84 captures with the real heads before the pairs.

Answer both from records you already hold (no new run, no Orchard call), in one event of at most 15 lines:
(a) Does a `program_refusal` row reach a token or timing validation in FULL mode as well? Name file:line either way.
(b) Projected pilot wall time against the limit: load and gates as measured in 169687, plus the measured geometry seconds per capture from 169670 times 84, plus twenty decodes at the budget cap (2,048 + 96 + 64 sampled tokens at the measured tokens per second). Give the total and its ratio to the limit.

Decision rule, so you do not wait on me:
- If (a) is yes, or (b) exceeds 70% of the limit: make ONE rebuild carrying both fixes. R1: rows with `finish == "program_refusal"` are skipped by the timing and token checks in pilot and full mode, counted in a reported field, and stay in every score denominator as they are now. R3: set the limit so the projection is at most half of it. Add tests that execute each changed line (a `program_refusal` row through `project` and `terminal`), rerun the whole-worker pilot rehearsal and the coverage review, and write the runtime diff against the current candidate as a file. I authorize one further replacement upload for that object; the queued upload of 4d05c37b is then not sealed (leave it to finish or sit; do not cancel it by hand).
- If (a) is no and (b) is at most 70%: seal the current object as planned and send the final review event; R1 stays a stated risk of the pilot.
Either way the final review event names the family SHA, the advanced token, and which branch you took. R2, R4 and R5 need no change; list them under "first executed on the GPU" in the event.