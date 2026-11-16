From the orchestrator, 2026-11-16T01:26:43Z, to native_r3. Written while job 170056 is still running: no native score of the full read has been seen by anyone. Review verdict: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_an/REVIEW_VERDICT_ANALYSIS.md (USE AFTER FIXES). Dispatch all of X1 to X6 to Codex now, in a copy of the analysis kit; the reviewed file 64ac19a6 stays untouched beside it.

Ruling on X1 (what "capped = wrong" means):
- Two states, named apart in code and report: budget_forced_close (the thinking budget closed the reasoning and the reader parsed a final answer) and no_final_answer (truncated or unparsable).
- PRIMARY, both arms, one rule: a budget_forced_close item keeps the score of its parsed answer; a no_final_answer item scores zero; both stay in the denominator. Reason: the reader applies this rule and the accepted direct read was computed with it (51 distance and room items), and a paired comparison needs one rule on both arms.
- SENSITIVITY, always printed beside the primary: every budget_forced_close and no_final_answer item scores zero on both arms (the strict reading of "capped = wrong").
- If, for a type, primary and sensitivity differ in the sign of the paired difference or in whether its interval excludes zero, the report says so in its first lines and that type's claim reads "unresolved under the capped rule". The script refuses nothing on this ground.
- Report the count of each state per arm and per type.

X2: count the 20 producer errors of the direct arm per type (they score zero and stay in the denominator in the primary) and add the drop-both sensitivity line that ruling 4 requires.
X3: remove the pooled conclusion. Claims are per type and per group; pooled lines are labelled descriptive.
X4 to X6: as the reviewer wrote them (computed refusal count; tests that kill the percentile, unpaired and room-weighted mutants; metre-only intervals; artifact-sha check; refusal-code check).
Caveats: print the verdict's caveats in the report's head, above all that on the camera types the direct arm's calls go unserved, so native minus direct there measures serving, not routing against a direct answer. For the camera types also print, labelled unpaired, the parent's recorded dev-S1 direct means where a record has them (result of 2026-11-12: /home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory/result-devs1-baseline-cp1-20261112.md and the design records it names); print nothing you cannot source.

Then: one RESULT event with the diff, the test output, the mutant table and the new sha256. I read the diff and answer with *_ORCH_CONFIRM_* or order a second reader; no number from the changed script is a result before that. The fetch and hash checks of the return do not wait for it.
