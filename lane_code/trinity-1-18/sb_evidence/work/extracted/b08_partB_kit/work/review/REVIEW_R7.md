VERDICT: NO-GO

References: **A** = [assign.py](/scratch/jjyeung/orch_n30/b08_headrows/code/headrows/assign.py); **V** = sealed [ground_v312.py](/scratch/jjyeung/orch_n30/rows_rebuild/work/tree/src/trace_format/ground_v312.py); **W** = sealed [ground_v313.py](/scratch/jjyeung/orch_n30/rows_rebuild/work/tree/src/trace_format/ground_v313.py).

**(a) R6 findings**

1. **FIXED — A:338–342.** Insert `<ground obj="table">\n` after the suffix’s opening `<think>\n`, leaving recorded events unchanged. Both the valid counting head and genuine recovery now drop as `record_unrecorded_tag`.
2. **FIXED — A:227–230.** With GT `{"chair":["chair:1"]}`, selected `{"chair":{"chair:1":false}}` now returns `direct:mask_mismatch:chair`. Setting both maps to `{"chair":"abc"}` returns `direct:mask_unverified`.

**(b) Verified current problems**

1. **High — Standard direction prose systematically rejects valid heads (A:341; V:211).**
   Use an eligible direction item with matching masks, published stand/face/query points `(0,0,1)`, `(0,0,2)`, `(-1,0,2)`, and the corresponding `<angle>` call.
   For medium, GT/prediction `"A"` names `"left"`; for hard, `"A"` names `"front-left"`.
   Include the sealed renderer’s exact sentence: `On the floor, cross > 0 means left; cross < 0 means right.`
   Both return `drop:record_unrecorded_tag`. Removing that sentence produces `head`.
   Both traces pass sealed packing, validation, and actual replay with unchanged receipts. The filter mistakes the renderer’s mathematical `<` for a tag.

2. **High — A truthful receipt does not establish the record’s declared version (A:278–286,303–304,332–335; W:236–237).**
   Start with a correctly replayed v3.12.2 absolute-distance record: ground chair and table, then `<gap a="chair" b="table">`, returning `"1.00 m"`; GT/prediction `"1.00"` and matching masks.
   Change only `record.spec_version` to `"3.14"`.
   Assignment still returns `head`; sealed packing and validation pass. Replaying through the original producing Session issues the identical receipt, even after the version change.
   A v3.14 Session rejects that exact gap call with `form_requires_v3.13`. Thus a correctly bound receipt admits a target incompatible with its declared grammar; no receipt was forged.

**Checked and found sound**

- **25 tests passed; one temporary-file-writing test was skipped.** Additional counterexamples ran in memory.
- All six pin hashes match. All 3,603 aliases agree with native eligibility; withheld aliases resolve to 80 rooms.
- Tested exclusions, rescan expansion, canonical room caps, minority selection, deterministic ordering, numeric boundaries, exact labels, and mask matching pass.
- Changed calls/responses and mismatched receipt function, `ok`, session hash, or events hash are rejected.
- Duplicate-ID refusal and recovery GT replacement are internally consistent with the docstring. Downstream recovery rendering was not verified.
- No files were edited; no SSH, Git, or network commands ran.