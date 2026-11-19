VERDICT: NO-GO

References: `A` = [assign.py](/scratch/jjyeung/orch_n30/b08_headrows/code/headrows/assign.py); `M` = [mask_match.py](/scratch/jjyeung/orch_n30/b08_headrows/code/headrows/mask_match.py); `G` = sealed `student_pilot/ground_rows.py`; `V` = sealed `trace_format/ground_v312.py`.
Inputs modify the supplied `item()`, `resp()`, `raster()` and `box()` fixtures. Event edits also update the corresponding suffix text.

(a) R3 findings—all eight reported counterexamples reproduced:

1. **FIXED — A:183,197.** GT `" 3 "` drops; prediction `" 3 "` against GT `"3"` produces `direct`.
2. **FIXED — A:167,181.** Numeric GT `"1e-1000000000"` with prediction `"0"` drops as malformed.
3. **FIXED — A:234.** Failure status `"chair: not seen"` with `record.not_seen=True` now produces `recovery`.
4. **FIXED — A:268.** Relative-distance GT/prediction `"B"` without `answer_content` drops.
5. **FIXED — A:266.** Item options `["A. right","B. left"]` versus record options `["A. left","B. right"]` drop.
6. **FIXED — A:294–296.** Call `<ground obj="table">` with status `"chair: not seen"` drops.
7. **FIXED — A:315–317.** Numeric GT `"-1"` drops before recovery assignment.
8. **FIXED — M:32.** Frame key `np.int64(10)` now matches instance 3 with IoU 1.0.

(b) Verified current problems:

1. **High — Malformed calls receive head/recovery (A:271,294; V:51,74–75).**
   Replace the call with `<ground obj="chair"`—omit the closing `>`. The success fixture returns `head`; the failure fixture returns `recovery`.
   Executing that exact call through the sealed `Session.execute` raises `malformed_ground_call`. Packing and prefix matching do not establish a valid runtime call.

2. **High — Head status is not checked against recorded failures (A:274–285,318–330).**
   Keep `status="ok"` and replace the wrapped event body with `"chair: not seen"` or `"mask_source_unavailable_for_type"`.
   Both return `head`. The copied trace contains a failure or explicitly excluded operator fault.

3. **High — Recovery accepts a nonexistent GT option (A:184,268,277–285,321–323).**
   Use relative-distance GT `"Z"`, fixture options A–D, failure `"chair: not seen"`, and record answer/content `"A"`/`"left"`.
   Assignment returns `recovery`. Replacing the final answer with GT `"Z"` leaves no corresponding option; sealed validation raises `KeyError: 'Z'`.

4. **Medium — Duplicate frame spellings inflate mask IoU (M:31–48).**
   Candidate `{10: box(0,4,0,4), 20: box(0,8,0,8)}` is unmatched at IoU 0.4. Adding `"10": box(0,4,0,4)` raises IoU to 0.5 and matches chair 3.
   Add a correct chair-5 candidate and use counting GT/prediction `"2"`: assignment changes from `direct` to `head` solely because frame 10 was counted twice.

5. **Medium — Null instance IDs count as verified grounding (A:207–213).**
   Set counting GT/prediction to `"1"`, both `gt_instances` and `selected` to `{"chair":[None]}`, and the event body to `"chair: 1 instances"`.
   Assignment returns `head`, although neither side supplies an actual instance ID.

6. **Medium — Valid operand names containing colons lose recovery rows (A:50,225; V:33–36,51–61).**
   Use operand `"chair: office"`, call `<ground obj="chair: office">`, and matching status/body `"chair: office: not seen"`.
   The sealed Session accepts the name and emits this failure; assignment drops it as `unknown_status`.

Checked and found sound:

- All six authorization hashes match. All 3,603 mapped aliases match their native eligibility results; withheld aliases resolve to 80 rooms.
- Supplied exclusion, room-cap, minority-selection, ordering, numeric-boundary, record-binding and ordinary mask tests pass.
- Duplicate-ID refusal and acceptance of a recovery record answer `"999"` are internally consistent with the docstring. The downstream recovery renderer was not verified.
- **21 tests passed; one file-writing test was skipped.** Counterexamples ran in memory. No files were edited; no SSH, Git or network commands ran.