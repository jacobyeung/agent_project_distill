# Design record: 64-frame variant of trainer tree N (sb_f64)

Status: built, not launched (2026-11-19). Needs one independent review: it changes row admission.

## Question
How does N's R1 training read 64 frames instead of 32 while its 32-slot heads, its init artifact
and the "frame i of 32" benchmark questions stay valid, and how does the read side see the same layout?

## Answer
Use a nested input: each row holds its 32 anchor frames plus the 32 frames that bisect the
anchors' largest gaps (`carrier_c1_data.nested_indices`, ties to the earliest gap, midpoint
`(a+b)//2`). The duplicate layout gives 64 temporal groups. Carriers, `Frame k: ` markers
(k = anchor ordinal 1..32), pose, depth and pointing targets and the question text sit on the
anchors; bisection groups carry pixels only. Config key `frame_input =
{viewpoints: 64, anchors: 32, rule: nested_bisection_v1}`; `frame_count` stays 32.

## Reasons and evidence
- N's init artifact binds 32-row pose, depth and query heads, and its loader refuses a shape change,
  so `frame_count: 64` would reinitialize those heads and drop N's lineage.
- Benchmark camera items name "frame i of 32" (read package A, `src/items/devs1_routed.json`).
  The nested set keeps those 32 frames, and uniform 64 sampling (`i*(T-1)//63`) does not.
- The tree already carries the nested rule for VQA (CP2 `nested-vqa-v1`, `evalpath/vqa_direct.py`).
  This change extends that rule to every multi-frame stream and makes the receipt declare it.
- The frozen ViT and the frozen private depth copy read anchors only (`frame_input.anchor_view`),
  so the extra memory is LM activations, which grow linearly with tokens.

## Options rejected
- `frame_count: 64` (64 carriers, 64-slot heads): head reinit, new init artifact, a new reader contract,
  and the "of 32" items no longer map onto carriers.
- Spread-64 (two viewpoints per temporal group, 32 groups, same token count): an earlier probe measured
  spread worse than duplicate on pose, and the read layout must match training.
- Nested VQA only (existing CP2 path): pose, routing and pointing would train on a 32-frame context
  while the reader shows 64, which breaks the user's rule that the read layout matches training.
- Markers on all 64 groups (numbered 1..64): question text names anchors 1..32, so the numbers would disagree.

## Risks and how we would notice
- Long text rows: 64 x 144 = 9,216 visual tokens at most; a row above about 11.5k tokens may pass
  the 76 GiB tripwire at world 4. The routing build admits suffixes up to 9,600 tokens, so a long
  routing row can also pass the 16,384 ceiling, and the R1 trainer aborts on that row instead of
  substituting it. `scripts/token_audit.py` encodes every distinct planned row on CPU before launch and
  lists rows over either bound; a nonempty list means deferring those rows (an admission change) or world 8.
- Pose jitter: anchors keep the 32-row augmentation draws and bisection frames draw afterwards;
  `test_f64_layout` pins this.
- Frame hosts must hold the bisection frames (decode cache). `nest_row` fails with
  `FRAME_INPUT_DENSE_FRAME_MISSING:<ordinal>` before any row reaches a store.
- A reader that builds 64 groups without `aux_anchor_groups` would put depth on bisection frames;
  `anchor_view` raises `FRAME_INPUT_ANCHOR_VIEW_SHAPE` when the grid and anchors disagree.

## Tests that settle it
`tests/test_f64_layout.py` (nest/check rows, anchor-only markers, anchor-only depth view, pose sample
check, training/read layout agreement, config comparison with pinned pixels), the focused build-18
suite on the patched tree, and the CPU dry run (`scripts/f64_dryrun.py`, evidence in `out/evidence/`).
