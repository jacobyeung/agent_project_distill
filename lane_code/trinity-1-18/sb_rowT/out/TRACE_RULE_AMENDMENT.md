The orchestrator must authorize this counting rule before training on the tally rows:

> For object_counting, permit either one Locate line per annotated distinct instance or a TALLY inventory for every asked category. In TALLY form, group annotated instances by their first-seen sampled-frame index. Within each category, emit each frame once in strictly increasing order, with an integer index in 1..32 and a positive integer count of newly seen distinct instances. Preserve supported left/middle/right tags as counts within that frame; those counts must sum to the frame count. End each category inventory with the sum of its frame counts. For multiple-category questions, print the sum of the category totals. The final answer must equal that sum. Never deduplicate instances merely because they share a frame or region. Do not introduce categories, frame citations, or counts absent from the source annotations.

Example:

```text
TALLY chair: frame 3: 2 (left: 1, right: 1); frame 7: 1 (middle: 1) -> 3.
```

Implementation requirements in the trainer kit:

- Extend `student_pilot/trace_grammar.py` to recognize this exact form and validate its arithmetic, frame order, region subtotals, and category coverage. Its existing explicit-list rule does not license tally counts.
- Extend `student_pilot/r1_counting.py` to admit validated TALLY inventories and validated Locate inventories for both single-category and `count_kind=total` rows. Its current gate rejects every total row and requires the literal procedure wording for single-category rows.
- Keep the direct store schema. `student_pilot/ground_rows.pack` expects a routed program record, which these sources do not contain. Use the native direct-row validator and the counting inventory checker; do not fabricate program evidence to pass the pack API.
- The `--form locate` option emits one Locate line per instance plus compact instance-tag lists followed by category counts, which license totals under the existing lexical grammar. This alternative still requires the counting admission change.

These changes have not been applied to W/w19. This artifact is a conversion kit, not a training-admission receipt. A finite valid tally does not guarantee that a model decoder terminates, and conversion does not establish visual counting accuracy.
