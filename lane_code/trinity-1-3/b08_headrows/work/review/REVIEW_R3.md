VERDICT: NO-GO

References: `A` = `code/headrows/assign.py`; `M` = `code/headrows/mask_match.py`; `G` = sealed `student_pilot/ground_rows.py`; `V` = sealed `trace_format/ground_v312.py`.
Inputs below modify the supplied `item()`/`resp()` fixtures; changed record answers also replace the suffix’s final answer.

(a) R2 findings, numbered as R2(b):

1. **FIXED — A:146,152,161.** Auxiliary identifiers `d1/scene0155_99`, `scannet++/09c1414f1b`, `scannet/scene0161_99`, and `d1/scene0183` now drop.
2. **FIXED — A:118–125.** Clean aliases `d2/v012679495aa0`, `d3/v00475f483e27`, and native `scannet++/00dd871005` now pass eligibility.
3. **FIXED — A:163,331.** Eight rows split between `d3/40777060` and `arkitscenes/40777060` now select four.
4. **FIXED — A:228,235.** `record.gt_agrees=False` and `record.training_admitted=True` drop; omitted flags are supplied during packing.
5. **FIXED for the reported inputs — A:233–239.** Missing `<think>`, `"not a call"`, unwrapped `"garbage"`, and version `"9.99"` drop.
6. **FIXED for the reported inputs — A:257,269–275.** Failure text appearing only in prose and missing final answers drop. A recovery answer `"999"` remains accepted consistently with the stated GT-replacement contract.
7. **NOT FIXED — A:189–192.** The original record/item GT discrepancy drops, but matching item/record GT `" 3 "` with prediction `"3"` still produces an invalid head; see (b)1.
8. **NOT FIXED — A:185–187.** The original `1.15000000000000000000000000001/1` case is fixed; exponent underflow still admits wrong answers; see (b)2.
9. **FIXED for fractional keys — M:31–34.** Candidate frame keys `10.5` and `20.5` now raise `ValueError`; an integer-type regression remains in (b)8.
10. **FIXED — A:181–187.** Numeric GT/prediction `"0"/"0"` produces `head`; `"0.01"/"0"` produces `direct`.
11. **FIXED under the current docstring — A:206.** Selected IDs `[chair:1,chair:2,chair:3,chair:3]` produce `direct`, as explicitly required.

R2(a)’s repeated findings are covered above. Its already-fixed option/count parsing, missing-operand, status, and provenance examples remain rejected at A:188–201,211–222,288–290. Both deliberate choices are internally consistent with the module docstring; the downstream recovery renderer was not verified.

(b) Verified remaining problems:

1. **High — Exact-string checks still trim whitespace (A:189–192; G:100–101).** Set item answer and record GT to `" 3 "`, retaining prediction/record answer `"3"`. Assignment returns `head`; `G.validate(A.sealed_pack(...))` raises `Grounding label mismatch`. Prediction/record answer `" 3 "` against GT `"3"` also passes assignment and fails validation.

2. **Medium — Decimal underflow silently accepts wrong answers (A:185–187).** Absolute-distance GT `"1e-1000000000"` and prediction `"0"` produce `head`, despite 100% error. Both sides of the tolerance comparison underflow to zero. Precision 200 does not establish exact arithmetic across accepted exponents.

3. **High — Genuine failure records are systematically refused (A:228,298; V:252).** Set `record.not_seen=True` on `resp(status="chair: not seen")`. Assignment drops with `sealed_pack_refused:record_flags`, although raw `G.pack` succeeds. The sealed runtime explicitly sets this flag on failures.

4. **High — Missing option metadata produces unusable heads (A:263; G:102).** Use relative-distance GT/prediction `"B"` and matching item/record options `["A. left","B. right"]`, without `answer_content`. Assignment returns `head`; sealed validation raises `KeyError: 'answer_content'`.

5. **High — Record options need not describe the item (A:248–265).** Give the item options `["A. right","B. left"]`, but record options `["A. left","B. right"]` and `answer_content="right"`; GT/prediction remain `"B"`. Assignment returns `head`, and sealed validation passes. The packed answer now denotes the opposite content from the item’s GT.

6. **High — Recovery text is not bound to the called operand (A:269–275).** In the failure fixture, replace `<ground obj="chair">` with `<ground obj="table">` in both event and suffix, retaining `"chair: not seen"`. Assignment returns `recovery`. Matching response text alone admits an inconsistent, unverifiable runtime failure.

7. **Medium — Recovery bypasses negative-GT exclusion (A:297–302).** Absolute-distance item/record GT `"-1"` with status `"chair: not seen"` returns `recovery`. The docstring requires negative numeric GT to drop; the recovery branch exits before that check.

8. **Medium — Valid NumPy integer frame keys are refused (M:31).** `match_candidate(raster(), {np.int64(10): box(0,4,0,4)})` raises `ValueError`, although frame 10 is pinned and the mask matches exactly. Keys taken directly from the supplied NumPy `frame_indices` therefore fail.

Checked and found sound:

- All six authorization hashes match. All 3,603 mapped aliases resolve and receive the same eligibility result as their native identifiers; withheld aliases resolve to 80 rooms.
- Original exclusion bypasses, ScanNet/ARKitScenes room caps, minority selection, cap ceilings, and reversed-input determinism pass.
- Ordinary mask mismatches, missing GT operands, duplicates, unknown frames, malformed records, operator faults, and malformed provenance are rejected.
- **19 tests passed; one temporary-file test was skipped.** Counterexamples ran in memory. No files were edited; no SSH, Git, or network commands ran.