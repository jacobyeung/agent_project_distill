VERDICT: NO-GO

References: **A** = [assign.py](/scratch/jjyeung/orch_n30/b08_headrows/code/headrows/assign.py); **G** = sealed [ground_rows.py](/scratch/jjyeung/orch_n30/rows_rebuild/work/tree/src/student_pilot/ground_rows.py).

(a) R5 findings:

1. **FIXED — A:253.** The original direction trace ending in `<angle S=P1 F=P2 Q=P3 rule=medium>` now produces `head`. Verified with published points, sealed calculator execution, and an actual replay receipt.
2. **FIXED — A:259,281,327.** `<ground obj=" chair">` fails name validation. `<surface_pair a="chair" b="table" mode="closest_visible">` under version 3.14 raises `form_requires_v3.13` and cannot earn a truthful receipt.
3. **FIXED — A:281,327.** Instance-mode grounding with a claimed `"chair: not seen"` response fails replay: the sealed Session actually prints `"chair: 0 found"`.
4. **FIXED — A:332.** Prepending a response containing `mask_source_unavailable_for_type` to the recovery fixture now drops as `record_operator_fault`.
5. **FIXED — A:345.** Heads containing `"chair: unresolved"` or `"chair: box unavailable"` now drop as `record_failure_in_head`. Verified using actual sealed Session responses and receipts.

(b) Verified current problems:

1. **High — Unrecorded calls survive replay and enter head/recovery targets (A:302,327; G:53).**
   Start with an eligible, correctly replayed one-chair counting record: GT/prediction `"1"` and matching `{"chair":["chair:1"]}`.
   Insert `<ground obj="table">\n` immediately after the suffix’s opening `<think>\n`, without changing `events`.
   Assignment still returns `head`; packing and validation pass. The target contains two ground calls, but only one is recorded or replayed. The table call becomes canonical text.
   The existing receipt remains valid, and replaying the modified record produces the identical receipt. The same insertion into a genuine chair-failure record returns `recovery`.
   Thus a truthful receipt permits copied calls whose execution was never verified.

2. **Medium — Malformed mask evidence passes as accepted IDs (A:226).**
   Keep the correctly replayed one-chair record and valid GT `{"chair":["chair:1"]}`; set `response.selected={"chair":{"chair:1":false}}`.
   Assignment returns `head`: `list(...)` silently converts the dictionary into its keys, accepting malformed evidence instead of the required ID list.
   Independently, setting both instance maps to `{"chair":"abc"}` also returns `head`, treating characters as instance IDs. Both counterexamples retain valid replay receipts.

Checked and found sound:

- **24 tests passed; one file-writing test was skipped.** Additional counterexamples ran in memory.
- All six pin hashes match. All 3,603 mapped aliases agree with native eligibility; withheld aliases resolve to 80 rooms. Tested exclusions and ScanNet rescan expansion pass.
- Numeric boundaries, exact labels, ordinary mask matching, duplicate rejection, canonical room caps, minority selection, and deterministic ordering pass.
- Changed calls/responses and mismatched receipt fields are rejected.
- Duplicate-ID refusal and recovery GT replacement are internally consistent with the docstring; downstream recovery rendering was not verified.
- No files were edited; no SSH, Git, or network commands ran.