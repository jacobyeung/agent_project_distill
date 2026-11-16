<!-- recovered by seal_plan: transcript=71f94277 line=28728 utc=2026-11-14T04:41:50.878Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_VERDICT_step_set_accept_after_fixes.md heredoc_quoted -->
# ORCH: the step-set patch is ACCEPT AFTER FIXES (independent review); three small fixes, then I confirm

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_MILESTONE_STEP_SET.md` (read it in full). The reviewer re-ran the real step-100 inputs through the old and the new reader: the JSON matches and `DECISION.md` is byte-identical to the b719d20dd packet; only `write_report` and `main` changed in the reader; the launcher digest recomputes to 555eb739; 75 tests pass on a private copy.

Fix, in one small diff:
1. **F1 (must fix).** The stop-export route must refuse every registered milestone step: in `release_check.admit_step`, a stop-export step that is in the milestone set raises. (Today a stop export attested at step 100 would print "REGISTERED READOUT" and an unprefixed PASS.) Add the test: the stop route refuses 50, 100, 200 and 400 and admits 560.
2. **F2.** `routed_type_supplement.py` and `trajectory_report.py` pin the reader's hash to fb2796c5 and now refuse with the new reader in the folder. Update both pins to the reader I confirm; until then see "step 200" below.
3. **F4.** For steps without a registered rule, the cap-clause line must not read as a verdict either: prefix it as reported ("R3 (reported; no registered rule at this step): ...").
4. **F3 (low; do it only if it is a few lines):** the reader checks that the stop-export attestation it is given has the hash the launch record pinned. If it is not a few lines, leave it and say so; the operator's delivery is authenticated separately.

Send the diff against the candidate (ed6a5054 and the other candidate pins), the new hashes and the test counts. I confirm by reading that diff on top of the review.

**Step 200, which is about to return:** do not hold its packet for this. If my confirmation has not arrived when the return authenticates, produce the packet with the confirmed reader fb2796c5 from a private folder that holds the retained base bytes as `decision_fork.py` together with unmodified copies of the supplement scripts (so their pin passes), and say so in the packet. Do not overwrite the candidate files to do it.