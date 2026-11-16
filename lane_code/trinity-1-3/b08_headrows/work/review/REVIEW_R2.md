VERDICT: NO-GO

References: `A` = `code/headrows/assign.py`; `M` = `code/headrows/mask_match.py`; `G` = sealed `student_pilot/ground_rows.py`. Inputs below modify the supplied `item()`/`resp()` fixtures unless stated otherwise.

(a) First-round findings:

1. **FIXED — A:167–171.** Options reject `"Banana"`, `"B but actually C"` and `None/None`.
2. **FIXED — A:167–169.** Counts reject fractional spellings and unequal integers beyond float precision.
3. **FIXED — A:176–185.** Declared operands missing from GT produce `direct`.
4. **NOT FIXED — A:134–144.** `room="scannet++/09c1414f1b"` produces `head` despite a sealed benchmark match; more bypasses below.
5. **FIXED — A:190–201.** Missing statuses and the original false-failure strings drop. Record-to-status binding remains defective.
6. **FIXED — A:243–245.** Empty pipeline names and malformed SHA-256 strings drop.
7. **NOT FIXED — A:146.** Eight rows for `arkitscenes/40777060`, split between room strings `d3/40777060` and `arkitscenes/40777060`, all survive selection.
8. **NOT FIXED against the original spec — A:164–165,257.** GT/prediction `"0"/"0"` now drops. The `0.85/1` boundary is fixed; the revised docstring explicitly excludes zero.
9. **NOT FIXED — A:225; G:100–101.** `record.gt_answer=" 3 "`, prediction/record answer `"3"`, item answer `"3"` produces `head`; sealed string equality fails.
10. **NOT FIXED — A:204–230.** `record.gt_agrees=False` or `record.training_admitted=True` still produces `head`; both violate G:81–82.

(b) Verified findings:

1. **High — Exclusion bypasses through auxiliary identifiers (A:134–144).**
   Each produces `head`: `room="d1/scene0155_99"` (sealed dev match); `room="scannet++/09c1414f1b"` (sealed benchmark match); `room="scannet/scene0161_99"` (withheld room); `room="d1/scene0183"` (R0 reserve).
   Auxiliary captures do not receive the sealed room-expansion check, `scannet++` is skipped, and R0 aliases are not normalized.

2. **High — Clean mapped aliases are systematically refused (A:111–118).**
   `dataset="d2", scene="v012679495aa0", room=None` drops as `canonical_ambiguous`; its pinned native `scannetppv2/216b9e55e8` is eligible.
   Likewise, `d3/v00475f483e27` drops while `arkitscenes/44796432` is eligible. The resolver incorrectly adds the alias token as another native identity.
   Across the pin, all 565 otherwise-clean mapped `d2` aliases and 1,308 mapped `d3` aliases suffer this refusal. Clean `dataset="scannet++", scene="00dd871005"` also drops as unknown.

3. **High — ARKitScenes aliases bypass the physical-room cap (A:146,286–290).**
   Eight distinct counting qids for `arkitscenes/40777060`, four with each room spelling from (a)7, produce eight selected heads. The required maximum is four.

4. **High — Invalid membership flags still pass head assignment (A:222–228; G:81–82).**
   Independently setting `record.gt_agrees=False` or `record.training_admitted=True` produces `head`. The fixture’s missing flags also fail the sealed predicate.

5. **High — Assigned heads can fail the sealed renderer (A:215–228; G:26–40).**
   Remove the suffix’s opening `<think>\n`, or replace the call with `"not a call"`, or replace its response with `"garbage"` in both event and suffix: each produces `head`.
   Reconstructing events as `pack` does and invoking `render_ground` rejects all three. `record.spec_version="9.99"` also passes assignment despite lacking a G:5–6 form.

6. **High — Recovery does not establish a failure event or a correct final answer (A:229,252–254).**
   Set status to `"chair: not seen"` but retain the successful event; inserting that text only as suffix prose produces `recovery`.
   A genuine failure fixture with record answer/final answer `"999"` and GT `"3"` also produces `recovery`. Removing the final answer entirely still produces `recovery`.

7. **High — Whitespace normalization admits a sealed-label mismatch (A:225; G:100–101).**
   Prediction/record answer `"3"` and `record.gt_answer=" 3 "` produce `head` against item answer `"3"`. The sealed validator compares the untrimmed strings and rejects them.

8. **Medium — Decimal context rounding admits an answer outside tolerance (A:166).**
   Absolute-distance GT `"1"` and prediction `"1.15000000000000000000000000001"` produce `head`. Exact arithmetic places the error above 15%; default Decimal precision rounds it onto the boundary.

9. **Medium — Fractional, unpinned frame indices are silently accepted (M:31–33,44).**
   On the supplied raster, chair masks keyed by `10.5` and `20.5` map to pinned frames 10 and 20. `selected_ids` returns both GT chairs, and counting GT/prediction `"2"` produces `head`, although neither supplied frame index exists.

10. **Medium — Zero-GT exclusion changes the original specification (A:164–165,257).**
    Absolute-distance GT/prediction `"0"/"0"` drops despite satisfying the original tolerance rule. This is an explicit revised restriction, not a repair under the first review’s spec.

11. **Medium — Duplicate rejection changes the original set semantics (A:185).**
    Selected IDs `["chair:1","chair:2","chair:3","chair:3"]` equal the GT set, but produce `direct`. These clean counting heads disappear from minority selection. The revised duplicate prohibition conflicts with the original set-equality requirement.

Checked and found sound:

- All six authorization-file hashes match their pins.
- All 16 read-only tests pass; the temporary-directory test was skipped.
- Original option/count counterexamples, missing-operand GT, ordinary mismatched masks, missing statuses, listed operator faults, and malformed provenance are rejected.
- ScanNet alias room caps, integer cap ceilings, minority-family selection, and reversed-input ordering pass.
- Ordinary mask IoU thresholds, integer unknown-frame rejection, and shape checks pass.
- No files were edited. Full packing/validation was not executed; renderer failures were reproduced directly, and validator incompatibilities follow from the permitted sealed code.