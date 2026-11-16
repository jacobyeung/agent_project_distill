# LEG-S1 step-100 decision rules: three clarifications made before any leg read (2026-11-13T19:02Z)

**Question.** An independent review of the decision code (`/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_DECISION_LOGIC.md`) found that the rule layer differed from the registered text in `/scratch/jjyeung/orch_cd/model_design_review/MODEL_IMPROVEMENT_PLAN_20261111.md` (lines 152 and 156) and that one clause could not fail. What exactly do the rules test?

**Answer (orchestrator, before any leg checkpoint was read; job 169097 was at about step 15).**
1. Stop rule scope: exactly seven types against f17 on dev-S1 (route planning, counting, relative direction easy/medium/hard, relative distance, object size). Relative count and relative size are reported and never stop the leg. Absolute distance and room size are routed types and belong to R1.
2. R3's cap clause: "hits the cap" is evaluated on budget-forced closes under the leg's own bounded 2,048-token thinking budget, printed both against the registered limit of 1 per 100 and as the paired difference leg minus parent. Output-cap hits with thinking on (16k) are printed beside it. The clause never stops the leg; its registered consequence (raise the direct share or shorten the budget at the next boundary) is triggered only when the leg is worse than the parent with the interval wholly above zero.
3. Deciding arms: each model under its own policy, as in the registered baseline: leg at the bounded budget against f17 with thinking on; leg against parent both at the bounded budget. The same-budget pairs are printed as a sensitivity table; a disagreement between the pairs on a tested type is reported at the top and ruled on then.

**Reasons and evidence.**
- The plan's line 152 names the seven tested types and says the two dev-only types "do not stop the leg"; the code stopped on every primary type. At step 0, f17 leads the parent on relative count by +15.1 [+4.4, +26.9], so a leg equal to its parent would have been stopped falsely.
- Under the bounded budget no answer can reach the output cap, so the code's count was zero by construction. The parent has 34 forced closes in 1,525 answers at the bounded budget (2.23 per 100) and 29 output-cap hits with thinking on (1.90 per 100): the absolute limit is exceeded before any leg training, so only a comparison with the parent carries information about the leg.
- The registered baseline (f17 73.50 against the parent 71.64) already compares own-policy arms; the parent's two arms differ by -0.36 [-0.85, 0.00] on dev-S1 primary.

**Options rejected.** Keeping the code as written (false stops; a vacuous clause). Deciding on same-budget arms only (changes the registered baseline after the fact). Dropping the absolute limit from the report (hides that the parent exceeds it).

**What might not work and how we would notice.** The two arm pairings could disagree on a tested type; the report's first lines say so. The list of the 47 scenes f17 saw is not yet a file; the exposure cut is a diagnostic until that list is hashed.

**Tests that settle it.** The reviewer's synthetic-f17 scope test; a forced-close count test on the parent's journals (34 of 1,525); the confirmation review of the forked decision code.

**Status.** Ruled; fixes ordered from the eval lane (`/scratch/jjyeung/orch_cd/evalx/inbox/`, file ending `ORCH_RULING_decision_logic_verdict_and_three_rulings.md`); confirmation review pending.

## Ruling 4: producer errors (2026-11-13T23:53Z, before any leg score was computed)

**Question.** The rehearsal read on the step-50 export (Orchard job 169311) returned completely, but the accepted decision code refused the bounded-budget arm: two absolute-distance records carry a producer error (the continuation's retokenization derivation failed; zero output tokens; score zero) and are neither tagged continuations nor missing items. How does the decision treat such records?

**Answer.** A record with an explicit producer error is its own disposition. (a) It stays in the denominator at its recorded score (zero) in the primary table. (b) It counts toward the cap clause only if its own record shows the first phase ended at the budget; the three counts (forced close, stopped unclosed, continuation error) print separately. (c) The read decides only if errors are at most 1% of the cohort in each deciding arm (15 of 1,525) and at most 2 in any one tested type; above that the stop rule is not evaluated and the keys are re-read after a producer fix. (d) A sensitivity line prints each tested type's leg-minus-f17 difference with error items removed from both arms; if the verdict differs between the two, the verdict is undetermined and the keys are re-generated before the orchestrator rules. (e) Comparator journals get the same treatment and their counts print, including zero.

**Reasons.** An empty answer scores zero under any official scorer, so the primary table stays what a reader of the benchmark would compute; a harness failure is still not a model failure, so a verdict must not rest on it. Two of 1,525 moves no tested type (both are absolute distance, which is routed and not tested), but the error depends on the generated text, so later checkpoints can hit it elsewhere.

