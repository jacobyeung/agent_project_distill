<!-- recovered by seal_plan: transcript=71f94277 line=33243 utc=2026-11-14T19:56:58.149Z kind=written original_path=/scratch/jjyeung/orch_cd/leg_s1_review/ORDER_ROUTED_READER_FIX_AFTER_PILOT6.md  -->
# ORCH order: fix the routed reader after pilot 6, then pilot 7 and the full read

Pilot 169605 (family 2b9d7815, step-200 export) passed the parity gate and read ten item pairs. An independent debugger then established, from the pilot's records, the code and a CPU replay over all items, why a full read is not yet meaningful. Read its record in full before touching anything: `/scratch/jjyeung/orch_cd/leg_s1_review/DEBUG_ROUTED_DISTANCE_REFUSALS_169605.md` (64 lines; replay script and output in `/scratch/jjyeung/orch_cd/leg_s1_review/work_debug_distance/`). Do not re-derive it.

## What is wrong (established)

1. **Candidate universe.** The reader gives the runtime the 8-key VSI-ScanNet vocabulary found in the question (perception.py:104,123,129 through `candidate_names`), while admission checks the capture's normalized mask-cache phrases. The runtime then refuses every other object name (routed_features.py:290-294, 312-313). 136 of 150 distance items have a scripted operand refused; the cache holds proposals for those names. Room items are unaffected.
2. **No bound on a decode that cannot answer.** After refused grounds the model repeated one gap call 198 times to the 200-call limit (14,754 tokens). The sealed decode refuses a token cap below 16,384, and `call_limit` is not counted as capped.
3. **Return size.** `decode.heads.ground_queries` is journaled in full (4.7 MB per room row), which alone projects 1.26 GB.

## The change I rule (reader and Orchard packaging only; the sealed trainer tree stays untouched)

A. **One list.** The runtime candidate universe of an item is the same list admission checks: the capture's normalized mask-cache phrases. Both arms use it. A scripted operand missing from the cache stays a `mask_cache_operand_missing` item refusal as the specification says (ROUTED_READ_SPEC_NOMDG.md lines 41-43); a model call outside the list is refused by the runtime as designed.
B. **Budget for the model's arm, equal to the direct read's own policy.** Through the existing `logits_processor` slot in `perception.generate`: after 2,048 generated token ids without `</think>`, force `\n</think>\n\n`; then allow at most 64 tokens; then force end of sequence. Bind the three numbers in the request. Count an item that hit the budget, and any `call_limit` finish, as capped in the report. The scripted arm does not decode and gets no limit.
C. **Journal.** Replace `ground_queries` in the returned rows by a digest (sha256, byte size, query count); keep the full field for the first three items of each type only.
D. **Projection.** Compute the full read's time from the per-item bound the budget implies, as the debugger did, and its size from the digested rows.
E. **Reporting, no scoring change.** Besides all items, report distance and room scores for the subset whose question asks metric units and the subset that asks other units (the room tool prints square metres only and the leg's rows are metric only; 7 of 36 room and 107 of 150 distance items ask other units). R1's arithmetic stays on all items.
F. **Which export.** The decision this read feeds is about the run's final state. If the family can bind the stop export of step 544 (`q8/8865619b/469ddece_mstop.tar`, artifact 1d6eeb28..., delivery proof `/scratch/jjyeung/orch_cd/orchard_cp2/out/EXPORT_STOP_DELIVERY_169097_m544.json`) by changing only the export's pins and the step value, build pilot 7 and the full read for step 544. If it needs more than that, say exactly what in your first event and build for step 200.

## Before any submission (lessons of six pilots; none is optional)

1. CPU replay of the scripted arm's grounding requests over all 150 distance and 36 room items against the new universe, with the debugger's `replay_universe.py` as the reference: the universe check must refuse none of the 300 operand checks that the cache-phrase check admits. Put the before and after tables in the event.
2. CPU tests for the budget: an item that never closes its thinking is forced to answer at 2,048 + 64; a normal item (the nine normal pilot decodes ended at 329 tokens or fewer) is byte-identical with and without the processor; the gap-loop trace of item vsi590k_161841, replayed with controlled token choices, ends at the budget and is flagged capped.
3. The pin list (now 46 rows) extended by every new or changed file, all rows with a disposition, through the reuse gate as for pilot 6.
4. Pilot 7's item selection must cover what pilot 6 could not: at least two distance items that were refused under the old universe (one where both operands were refused), one room item in square feet, one in square metres, and four camera items; ten pairs in total.
5. One event with the runtime diff and test diff (paths, sha256), the replay tables, and the projection. I start one independent review at once (the candidate universe and the budget change what the read measures). Seal, upload and build the `advanced` pilot packet meanwhile; submission waits for the review's ACCEPT and my control files, as before.

## Not in this change (record for the next training seal, do not build)

The tools print metric units only and no training row asks another unit or shows a failed ground; both are properties of the leg's data, not of the reader.

## Slots

P0 169530 runs on `general` (its return goes to if_p0). Pilot 7 goes to `advanced` under the same account rule as pilot 6 (main's eight protected jobs only while pending for Dependency or JobHeldUser). A full read on `advanced` needs my separate order, after I have told main.
