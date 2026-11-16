VERDICT: NO-GO

References: `A` = [assign.py](/scratch/jjyeung/orch_n30/b08_headrows/code/headrows/assign.py); `M` = [mask_match.py](/scratch/jjyeung/orch_n30/b08_headrows/code/headrows/mask_match.py). `V` and `W` denote the permitted sealed `trace_format/ground_v312.py` and `ground_v313.py`.
Inputs modify the supplied `item()`, `resp()`, `raster()` and `box()` fixtures. Event edits also update the suffix.

(a) R4 findings—all six reported counterexamples are fixed:

1. **FIXED — A:288.** Call `<ground obj="chair"` now drops as `record_call_grammar` for both success and recovery.
2. **FIXED — A:303.** With `status="ok"`, recorded body `"chair: not seen"` or `"mask_source_unavailable_for_type"` now drops as `record_failure_in_head`.
3. **FIXED — A:191.** Relative-distance GT `"Z"` with options A–D and a failure record now drops as `gt_not_an_option`.
4. **FIXED — M:36.** Candidate `{10: box(0,4,0,4), 20: box(0,8,0,8), "10": box(0,4,0,4)}` now raises `ValueError`.
5. **FIXED — A:218.** GT/prediction `"1"` with both instance maps `{"chair":[None]}` now returns `direct:mask_unverified`.
6. **FIXED — A:50,323.** Operand `"chair: office"`, matching ground call and status `"chair: office: not seen"` now produce `recovery`.

(b) Verified current problems:

1. **High — Valid direction calculators are systematically refused (A:244,288; V:212).**
   A medium-direction record grounds stand/face/query at published points `(0,0,1)`, `(0,0,2)`, `(-1,0,2)`, then executes `<angle S=P1 F=P2 Q=P3 rule=medium>`.
   The sealed Session returns `theta 45 deg; left`. With matching masks, option `"A. left"` and GT/prediction `"A"`, sealed packing and validation pass, but assignment drops as `record_call_grammar`.
   The whitelist omits `<angle>`, which the sealed direction renderer emits.

2. **High — Regex-valid calls can still be invalid runtime calls (A:288; V:33; W:236).**
   Replace the successful fixture’s call with `<ground obj=" chair">`: assignment returns `head`; sealed execution raises `invalid_object_name`.
   Alternatively, retain version `"3.14"` and use `<surface_pair a="chair" b="table" mode="closest_visible">`: assignment returns `head`; execution raises `form_requires_v3.13`.

3. **High — Recovery accepts a response that its call cannot emit (A:323; W:259).**
   In `resp(status="chair: not seen", pred=None)`, change the call to `<ground obj="chair" mode="instances">`.
   Assignment returns `recovery`. Executing that call with zero resolved instances returns `"chair: 0 found"`, not the claimed failure. Matching only the object name does not verify the runtime status.

4. **High — Recovery retains earlier operator faults (A:300,317).**
   Prepend event `{call:'<ground obj="table">', response:'<tool_response>\nmask_source_unavailable_for_type\n</tool_response>'}` to the ordinary chair-failure record.
   Assignment returns `recovery`. Operator-fault scanning runs only for heads, so this explicitly excluded fault survives in the recovery trace.

5. **High — Heads retain unresolved or unavailable responses (A:303; W:274).**
   Keep `status="ok"` and replace the successful fixture’s wrapped response body with `"chair: unresolved"` or `"chair: box unavailable"`.
   Both return `head`. These are runtime failure states, but the head check recognizes only `"<name>: not seen"` and the four operator-fault strings.

Checked and found sound:

- **22 tests passed; one file-writing end-to-end test was skipped.** Additional counterexamples ran in memory.
- All six pin hashes match; all 3,603 mapped aliases agree with native eligibility results; withheld aliases resolve to 80 rooms.
- Tested exclusion gates, canonical room caps, minority selection, deterministic ordering, numeric boundaries, exact labels, record binding and ordinary mask checks pass.
- Duplicate-ID refusal and recovery GT replacement are internally consistent with the docstring. The downstream recovery renderer was not verified.
- No files were edited; no SSH, Git or network commands ran.