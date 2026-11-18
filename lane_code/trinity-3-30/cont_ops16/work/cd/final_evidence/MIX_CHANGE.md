# Counting fix for leg R1: mix and store change (lane count_diag, 2026-11-18)

Cause: single-category counting rows in store v7 teach a first-seen list ("locate each distinct X at its first appearance: frame 1; frame 1; ...") whose entries repeat. R1 m100 writes the list on 137/150 dev-S1 and 246/287 R0-dev single items and loops on one entry until the token cap on 28/150 and 68/287. Detail: `R1_COUNTING_LOSS_DIAGNOSIS_20261118.md`.

All REMOVE files use the sealed Removals format of `n.json` (one JSON object per line: pool, question_type, reason, row_key = qid, scene); none repeats a qid of `n.json` 02315a74, so they stack with it. Reason string: `count_diag_first_seen_list_form` (r1_ops5 confirms the kit accepts a new reason value; otherwise reuse any accepted value, the match is by row_key).

## B1. Continuation from R1's step-200 export (REMOVE list only; store v7 unchanged)
- `COUNT_FIX_REMOVE_B1.jsonl` (17,879 rows; sha256 25c3db82b4c590a39924b6b9636b7b4372cf91134a6242fe9895daaca179ceba): every counting-family row whose target is a first-seen list.
  - r1g single rows with a first-seen list: 6,636 (rows_a2's 6,552 retraced rows + D0's 84 GT-list rows)
  - b12 single rows (region form): 2,042 (2,113 less the 71 already in n.json)
  - b12 totals: 7,962 (8,064 less 102 in n.json); D0 gap totals: 1,239
- Cells: counting = min(10.87, 4 x 2,617 / 1,000) = 10.46 rows per step (hundredths at or under the ceiling 10.468) over the 2,617 procedure-only rows ("find each distinct X, across the frames, and count it once" / "find the distinct instances of X; count each once across the frames"); totals 0 (no eligible row). Freed VQA slots (0.41 + 3.39) refill direction under the card's rule. first_seen 2.00, appearance 14.42 and every other cell unchanged.
- Repeats: 10.46 x 800 / 2,617 = 3.2 draws per row over steps 201-1,000, plus about 0.19 per row already drawn in steps 1-200 (2.52 per step): under the card's 4.
- Variant `COUNT_FIX_REMOVE_B1_keepD0totals.jsonl` (16,640; sha256 56e5987d42b137a5379f7fe3d6f21c31b6f7d02461f3d7132d6afabcffeac6f3): keeps D0's 1,239 totals rows; set the totals cell to 1.00 (D0's dose). Use it only if the orchestrator prefers D0 parity on multi-category questions to removing the loop source there.

## A. Relaunch from step 544 (store change + REMOVE list)
- Store v8 = v7 with the 6,552 rows_a2-retraced counting rows given back their D0 v5 target: `COUNT_FIX_RESTORE_V5_TARGETS.jsonl` (6,552 rows; sha256 81b2a89d1c07d80007f61d0a06d552ed3ad1b70ae85771e14c9ca24e155eb017; fields i_v7, i_d0v5, qid, v7_target_sha256, restore_target, restore_target_sha256). Every restore target was checked three ways: equal to A2 v3 CHANGES `old_target`, sha256 equal to the row's `retrace_a2.d0_v5_target_sha256`, and equal to the row of D0 v5 store 4af43b40 (`rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite`); all are procedure-only. Only the target changes; question, answer, frames and qid stay.
- `COUNT_FIX_REMOVE_A.jsonl` (11,327 rows; sha256 6d5278cdeed38367fdda680c2a699864ab79905d3d594bff9eb5d8ea24fdd3fc): D0's 84 GT-list single rows, b12 single 2,042, b12 totals 7,962, D0 gap totals 1,239.
- Cells: counting 10.87 over 9,169 procedure-only rows (ceiling 36.676; about 1.2 draws per row in 1,000 steps); totals 0, its 3.39 refills direction. Everything else as R1.
- If no store change can be made before the relaunch, use B1 for the relaunch too (counting 10.46 over 2,617 rows, about 4 draws per row).

## Expected effect and its basis
- Single counting returns to D0's form and level: D0 m100 and H1-1 m100, which drew this form at 7.73 rows per step, beat step 544 by +9.20 [+4.53, +13.96] and +9.27 [+4.86, +13.74] on R0-dev single items and by +5.67 [-0.87, +11.69] and +3.73 [-2.12, +9.11] on dev-S1, with 0 single-item runaways of 437; D0 m200 holds +9.44 [+5.28, +13.73] on R0-dev single.
- The single-item loop needs the list form: D0 and H1-1 loop only on multi-category items (34 and 39 of 98), where their totals rows trained the list.
- Removing totals removes the only remaining list-form source; multi-category accuracy without totals rows is unmeasured (step 544, trained without totals, scores 31.4 on the 98 items; the list-form lineages score 17.4 to 26.3).

## What cannot be known without a read
- How fast the continuation unlearns 200 steps of the list form (D0 switched its size template within about 820 rows, about 80 steps at 10.46 per step); the m400 read shows it as the single-item runaway count, which should fall towards 0.
- Multi-category counting without totals rows (98 R0-dev items, 18% of the pooled counting statistic).
- Whether the procedure-only form, which the rows reviewer judged answer-only in substance, is acceptable under the trace ruling for this leg: an orchestrator decision.
