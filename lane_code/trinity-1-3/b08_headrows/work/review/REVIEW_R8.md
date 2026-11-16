VERDICT: NO-GO

References: **A** = [code/headrows/assign.py](/scratch/jjyeung/orch_n30/b08_headrows/code/headrows/assign.py); **V** = sealed [trace_format/ground_v312.py](/scratch/jjyeung/orch_n30/rows_rebuild/work/tree/src/trace_format/ground_v312.py).

(a) R7 findings:

1. **FIXED — A:349.** Reproduced medium/hard direction traces with points `(0,0,1)`, `(0,0,2)`, `(-1,0,2)` and the sentence `On the floor, cross > 0 means left; cross < 0 means right.` Both now receive `head` with actual replay receipts; their packed rows validate.

2. **FIXED — A:276–294,339–343.** Changing only a correctly replayed distance record’s version from `3.12.2` to `3.14` now produces `drop:record_replay_missing`. Requesting a replacement receipt from the original Session raises a version-mismatch error. A compatibility regression remains below.

(b) Verified current problem:

1. **High — Receipt creation systematically rejects native v3.12 Sessions (A:289–291; V:43–48,252).**
   Failing input: eligible `scannet/scene0232_02`, medium direction, GT/prediction `"A"`, options `["A. left","B. right"]`, matching chair/table/sofa instance IDs.
   Ground those objects at `(0,0,1)`, `(0,0,2)`, `(-1,0,2)`, then execute `<angle S=P1 F=P2 Q=P3 rule=medium>` through either sealed `ground_v312.Session` implementation.
   The resulting `spec_version="3.12.2"` record passes actual replay, packing and validation.
   Nevertheless, `replay_receipt(record, fresh_session, pipeline_sha256)` raises `ValueError: session spec_version None differs from record '3.12.2'`.
   Neither legacy Session defines that attribute; its renderer supplies the `3.12.2` default explicitly. These valid records cannot obtain the required receipt, preventing eligible direction heads from entering selection.

Checked and found sound:

- **27 tests passed; two file-writing tests were skipped.** Additional probes ran entirely in memory.
- All six pin hashes match. All 3,603 aliases agree with native eligibility; withheld aliases resolve to 80 rooms.
- Tested exclusions, physical-room caps, minority selection, deterministic ordering, numeric boundaries, exact labels and mask checks pass.
- Receipt-field mutations and changed calls, responses, event order or audit metadata are rejected. No different-events binding bypass was found.
- Unrecorded calls are rejected. Genuine recovery records retain valid receipts and pass the tested exclusion gates.
- `build_rows.pack_head` produces validating medium/hard direction rows from actual replayed records.
- Duplicate-ID refusal and recovery GT replacement are internally consistent with the docstring. Downstream recovery rendering remains unverified.
- No files were edited; no SSH, Git or network commands ran.