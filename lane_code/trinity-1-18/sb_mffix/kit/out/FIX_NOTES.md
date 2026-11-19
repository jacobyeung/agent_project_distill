# Review corrections

All six reporting corrections are applied. Candidate availability matches the reviewer at all three IoU thresholds. The additional track-majority diagnostic differs from F1; both counts and the missing reviewer recipe are disclosed below. No rule, threshold, pricing function, or endpoint changed.

- F1: Marked wrong_instance structurally empty and reported the reviewer’s 140 wrong-object tracks / 803 selected-track-absent frames. The kit pooled-pixel majority helper yields 107 / 677. It pools nonnegative GT IDs across selected proposal pixels; the reviewer’s counting recipe is MISSING from the supplied compare.py and rerun.py, so this discrepancy remains unresolved (F1_COMPARISON.json). `out/FIRST_TABLE.md:14`.
- F2: Recomputed candidate availability through Objects.load and routed_candidates.lift at floor 0.3: 1,487 accepted-track frames, 156 passing the floor outside accepted tracks, and 458 below the floor. Only 1,487 count as selection failures; 614 need proposal-filter changes. `out/MASKFAIL_REPORT.md:60`.
- F3: Stated beside the teacher column that its pool is a subset of the deployed pool. Item 5 uses deployed candidates alone; retained threshold-0.7 mask discrepancies are not independent proposal evidence. `out/MASKFAIL_REPORT.md:58`.
- F4: Renamed the displayed category selected track absent and reported candidate availability: 963 absent, 275 outside accepted tracks, and 1,155 selectable. The intervention remains an upper bound. `out/FIRST_TABLE.md:18`.
- F5: Added independent/cumulative refusal counts and point effects: 36 A0 refusals contribute +2.8544 no_proposal points; 119 new wrong_class refusals cost 2.6905 points after 588 GT-absent masks are emptied. `out/FIRST_TABLE.md:16`.
- F6: Filled every Rows cell with distinct row IDs; the caption states that group membership includes GT-absent records and area groups can overlap in rows. `out/SPLITS.md:7`.

Implementation: `recompute.py:12` computes availability and reprices endpoints; `finalize.py:31` verifies all 2,074 predictions against PER_ITEM and all cumulative closures. `run.sh:3` sets the working directory to this copy.

Commands: `bash run.sh recompute.py` and `bash run.sh finalize.py`, from kit/ (or the extracted archive root). Original overlap, classification, and intervention commands are recorded in MASKFAIL_REPORT.md.

The source kit remains read-only. Copied measurement JSON retains its original input hashes; RECOMPUTED.json, FRESH_ENDPOINT_PARITY.json, REFUSAL_EFFECTS.json, and VALIDATION.json record hashes for the new computations.

No reader-facing revision-history passages were retained; this requested correction log records the changes.
