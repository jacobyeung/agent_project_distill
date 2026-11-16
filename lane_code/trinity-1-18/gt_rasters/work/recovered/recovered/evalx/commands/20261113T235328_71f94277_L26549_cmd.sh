<!-- recovered by seal_plan: transcript=71f94277 line=26549 utc=2026-11-13T23:53:28.304Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_RULING_submit_step100_now_and_producer_error_disposition.md <<'EOF'
# ORCH ruling on BLOCKER 2350Z: submit the step-100 read now; producer errors get their own disposition

## 1. Submit step 100 now

The refusal is in the CPU decision reader, not in generation. The rehearsal proved the whole GPU chain and its return. The slot is free, so submit the prepared package `work/milestone/submissions/b719d20dd/` once, now, unchanged. Do not wait for the reader. Report the job id and the staging result as before.

## 2. Ruling 4 (fixed now, before any leg score has been computed): a producer error is its own disposition

A record that explicitly carries a producer error (here: a retokenization derivation error with zero output tokens and an empty generation) is neither a successful continuation nor a missing item. The reader accepts it only as disposition `producer_error`, identified by the explicit error fields, never by guessing. Then:

- **Primary table.** The item stays in the denominator with the score the journal recorded (zero). Nothing is relabelled and nothing is dropped.
- **Cap clause (ruling 2).** A producer error counts as an answer that reached the bounded budget only if its own record shows the first phase ended at the budget (forced close or stopped unclosed). If the record cannot show that, list it as "error, phase unknown" and count it on neither side. Print the three counts separately: forced close, stopped unclosed, continuation error.
- **Validity bound.** The read decides only if producer errors are at most 1% of the cohort in each deciding arm (15 of 1,525) **and** at most 2 items in any one of the seven tested types. Above either bound the stop rule is not evaluated; the affected keys are re-read after the producer is fixed.
- **Sensitivity line.** For each tested type, also print the leg-minus-f17 difference with every error item removed from both arms (paired). If the stop verdict differs between the primary table and the sensitivity line, the reader's verdict is `UNDETERMINED_PRODUCER_ERRORS`, and I rule only after those keys are re-generated (a rerun of fewer than 1,000 questions needs no further word from me or the user).
- **All arms alike.** Apply the same disposition to the parent and f17 comparator journals and print their error counts, including zero.

Any other unidentified record keeps refusing, as now.

## 3. Reader change and confirmation

Implement ruling 4 in the decision fork as the smallest change, with tests that include: the two real step-50 records; an error record whose first phase did not reach the budget; an error count above each validity bound; a verdict that flips between primary and sensitivity. Deliver the diff against 86c91ea8, the new hash and the test result. I confirm it by reading the diff, and only then may any leg score be computed, the step-50 diagnostic included. Do not run the fork on the step-50 or step-100 returns before my confirmation.

## 4. The producer's error branch (not blocking step 100)

Report the cause in a few lines: what the derivation does, why these two outputs fail it, whether the error depends on the generated text (so other items can hit it at step 100), and the smallest fix. A producer change alters accepted launcher code, so it needs its own confirmation and applies from the step-200 read at the earliest. Also state: 126 tagged continuations at step 50 against the parent's 40 on the same cohort, by type, as a count only (no scores).
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> $C/ORCH_HANDOFF.md <<EOF
$T orch-home-distill-79: evalx BLOCKER 2350Z: rehearsal job 169311 COMPLETED its whole chain 23:37:45Z and returned a 39.2 MB archive (sha 8ae926ce; verifier pass; eight receipts). The accepted decision fork refuses main/B2048 ("Unidentified bounded-policy continuation"): two absolute-distance records (devrows:vsi590k_155745, _256028) carry a producer retokenization-derivation error (zero output tokens, score zero); 126 tagged continuations at step 50 (parent 40). Step 100 was held. RULING ($N): (1) SUBMIT step-100 package b719d20dd NOW (the refusal is in the CPU reader; the GPU chain is proven); (2) RULING 4, fixed before any leg score: producer_error is its own disposition, stays in the denominator at zero in the primary table; counts toward the cap clause only if its record shows the first phase ended at the budget; validity bound 1% of the cohort per deciding arm and 2 per tested type; paired-exclusion sensitivity line; verdict UNDETERMINED_PRODUCER_ERRORS if primary and sensitivity disagree, then re-read those keys; same for comparator arms; (3) reader diff vs 86c91ea8 to me for confirmation before any score is computed; (4) cause of the producer error and the continuation counts by type owed, not blocking.
$T orch-home-distill-79: orchard_cp2 RESULT 2349Z: bundle d93d0359 verified (15 index pins); held production metadata (step 169097.2, 19:56:22Z) proves the staged interpreter resolves to /usr/bin/python3.12 (regular file, 8,020,928 B). RESULT 2349Z final-hour working budget out/FINAL_HOUR_BUDGET_169097_20261113T234025Z.json (sha 17e95626): save 77 s + packing allowance 300 s + export 69.7 s + slot write 410.7 s at 275 MB/s; working total 27.85 min (not a deadline bound). Re-armed evwait (bsmtf4nh6).
EOF
echo $N