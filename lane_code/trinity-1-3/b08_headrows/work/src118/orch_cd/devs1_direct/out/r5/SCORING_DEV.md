The adapter changes only summaries for `benchmark == devrows`. It calls the kit's original merge and budget merge, then rescales no item scores. Official types use the kit's official rescorer; the two dev-only types use exact option-letter matching. The wrapper checks that every summary score equals the admitted journal score.

| Dev question type | Score after kit extraction | Implementation (file:line) |
|---|---|---|
| object_abs_distance | Unchanged official numeric MRA | `aws_vl64rt/evaluator/scoring.py:92`; `aws_eval_gaps/evaluator/scoring.py:90`; `evalpath/official.py:269` |
| object_counting | Unchanged official numeric MRA | `aws_vl64rt/evaluator/scoring.py:92`; `aws_eval_gaps/evaluator/scoring.py:90`; `evalpath/official.py:269` |
| object_size_estimation | Unchanged official numeric MRA | `aws_vl64rt/evaluator/scoring.py:92`; `aws_eval_gaps/evaluator/scoring.py:90`; `evalpath/official.py:269` |
| room_size_estimation | Unchanged official numeric MRA | `aws_vl64rt/evaluator/scoring.py:92`; `aws_eval_gaps/evaluator/scoring.py:90`; `evalpath/official.py:269` |
| object_rel_direction_easy | Unchanged official exact match | `aws_vl64rt/evaluator/scoring.py:87`; `aws_eval_gaps/evaluator/scoring.py:85`; `evalpath/official.py:257` |
| object_rel_direction_medium | Unchanged official exact match | `aws_vl64rt/evaluator/scoring.py:87`; `aws_eval_gaps/evaluator/scoring.py:85`; `evalpath/official.py:257` |
| object_rel_direction_hard | Unchanged official exact match | `aws_vl64rt/evaluator/scoring.py:87`; `aws_eval_gaps/evaluator/scoring.py:85`; `evalpath/official.py:257` |
| object_rel_distance | Unchanged official exact match | `aws_vl64rt/evaluator/scoring.py:87`; `aws_eval_gaps/evaluator/scoring.py:85`; `evalpath/official.py:257` |
| route_planning | Unchanged official exact match; own-GT view only when no released label exists | `aws_vl64rt/evaluator/scoring.py:87`; `aws_eval_gaps/evaluator/scoring.py:85`; `report.py:96` |
| relative_count | Exact match of a valid displayed option letter; empty or invalid option is zero | `dev_scoring.py:11`, `dev_scoring.py:33`; kit item scorer at `scoring.py:87` (CP1), `scoring.py:85` (f17) |
| relative_size_object | Exact match of a valid displayed option letter; empty or invalid option is zero | `dev_scoring.py:11`, `dev_scoring.py:33`; kit item scorer at `scoring.py:87` (CP1), `scoring.py:85` (f17) |

Kit paths are relative to `/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3`. `evalpath/official.py` is inside each kit's `evaluator` directory; the cited extraction and metric lines are identical in both kits. Adapter/report paths are relative to this `out/r5` directory.

The kit extracts the suffix after the last closing think tag, then its answer tag or final line (`evalpath/official.py:52`). Its first-token convention splits on a literal space, removes trailing periods, and strips whitespace (`:252`). Exact match ignores letter case (`:257`). Thus `A` and `A.` parse; arbitrary prose or a letter outside the displayed choices does not earn credit. The extension adds no alternative extraction heuristic.

MRA is the kit's mean of relative-error threshold hits, using its existing floating-point implementation and inclusive comparisons. Invalid numeric predictions score zero. A zero numeric target scores one only for a zero prediction. The extension calls the original function rather than reproducing this calculation.

`tokens >= cap` or `finish_reason == length` records a cap hit independently of score. A parsed capped answer can earn credit. Thinking without a closing tag yields an empty answer and zero credit. Empty, invalid, and authenticated failed-derivation rows remain in the completed denominator. Ordinary rows are checked against `raw_generation`; CP1 additionally decodes token IDs and validates its 4,096-token prefix. f17 retains its reviewed kit's own admission checks; that kit has no `token_audit.py` or tokenizer argument.

The unchanged CP1 budget merger authenticates source rows, source and record hashes, receipts, budget bindings, prefix tokens, and forced-close tokens. Continuations allow at most 64 answer tokens. Early-close reuse retains the complete ON row, including answers longer than 64 tokens and the original ON cap. Failed derivations remain unanswered zero-score rows. See the governing [SEMANTICS.md](/scratch/jjyeung/orch_cd/rv_merge_fix/out/r2/SEMANTICS.md).

Dev overall is the item-weighted mean over completed items (`dev_scoring.py:53`). It is not an official VSI benchmark aggregate. Eligible reports require all expected tasks and passing parity. The primary report uses the mapped released label in the displayed option order. Routes have no released label and remain outside primary, with their own-GT scores retained separately. Pass-4 controls use their own label and stratum.

Reports count unparsed answers with the kit's diagnostic for official types and valid-option membership for the two dev-only types. The kit flags only empty MC first tokens as parse failures; a nonempty invalid dev option is additionally counted as unparsed by the report. This diagnostic refinement changes neither journal bytes nor scores. `parse_failures` in the kit-shaped summary retains the kit diagnostic; `dev_option_parse_failures` states the stricter dev count separately.

No kit file or official type registry is patched. `dev_scoring.installed()` temporarily replaces only the two imported summary aliases and restores them on exit, including exceptions. Every non-dev benchmark delegates directly to the original summary callable. `BYTE_IDENTITY.json` and the integration tests verify both reviewed kit inventories and their copied runtime files.
