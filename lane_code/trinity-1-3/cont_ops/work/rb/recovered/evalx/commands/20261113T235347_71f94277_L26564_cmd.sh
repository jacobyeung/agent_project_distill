<!-- recovered by seal_plan: transcript=71f94277 line=26564 utc=2026-11-13T23:53:47.000Z kind=commands original_path=(bash command)  -->
F=/data2/jjyeung/agent_project_data/distill_design/LEGS1_M100_DECISION_RULE_CLARIFICATIONS_20261113.md; cat >> $F <<'EOF'

## Ruling 4: producer errors (2026-11-13T23:53Z, before any leg score was computed)

**Question.** The rehearsal read on the step-50 export (Orchard job 169311) returned completely, but the accepted decision code refused the bounded-budget arm: two absolute-distance records carry a producer error (the continuation's retokenization derivation failed; zero output tokens; score zero) and are neither tagged continuations nor missing items. How does the decision treat such records?

**Answer.** A record with an explicit producer error is its own disposition. (a) It stays in the denominator at its recorded score (zero) in the primary table. (b) It counts toward the cap clause only if its own record shows the first phase ended at the budget; the three counts (forced close, stopped unclosed, continuation error) print separately. (c) The read decides only if errors are at most 1% of the cohort in each deciding arm (15 of 1,525) and at most 2 in any one tested type; above that the stop rule is not evaluated and the keys are re-read after a producer fix. (d) A sensitivity line prints each tested type's leg-minus-f17 difference with error items removed from both arms; if the verdict differs between the two, the verdict is undetermined and the keys are re-generated before the orchestrator rules. (e) Comparator journals get the same treatment and their counts print, including zero.

**Reasons.** An empty answer scores zero under any official scorer, so the primary table stays what a reader of the benchmark would compute; a harness failure is still not a model failure, so a verdict must not rest on it. Two of 1,525 moves no tested type (both are absolute distance, which is routed and not tested), but the error depends on the generated text, so later checkpoints can hit it elsewhere.

**Options rejected.** Relabelling errors as continuations (false provenance). Dropping them from the denominator in the primary table (changes the cohort after the fact). Holding the GPU read until the reader was fixed (the refusal is in the CPU reader; the read was ordered submitted at once).

**What might not work.** The 1% and 2-per-type bounds are judgment, not derived; a type with few items could flip on two items, which the sensitivity line exposes. The cause of the derivation error is not yet traced.

**Status.** Ordered from the eval lane (`/scratch/jjyeung/orch_cd/evalx/inbox/20261113T2353Z_ORCH_RULING_submit_step100_now_and_producer_error_disposition.md`); the reader diff awaits the orchestrator's confirmation before any score is computed.
EOF
I=/data2/jjyeung/agent_project_data/distill_design/INDEX.md; grep -n 'LEGS1_M100_DECISION_RULE' $I | cut -c1-300