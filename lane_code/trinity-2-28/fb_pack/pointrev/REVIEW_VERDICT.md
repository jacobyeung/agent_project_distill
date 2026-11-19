**Verdict: GO AFTER FIXES.** The new store meets the ruling on all 25,020 rows, but the handoff never delivers the Locate line to training: the R1 production admission rebuilds the pointing stream and erases it (MUST 1).

Evidence: my own scripts `work/check_rows.py` and `work/native_gates.py`, with outputs `work/*.json`. Every packet file matches its `.sha256`.

## Checks
1. **Diff (PASS).** In every row, `i` and order match. The `rows.row` bytes are identical outside the `target` string literal. The auxiliary `rows.target` column (`{}`) and the schema are unchanged. Every old think block was empty, and the answer bytes after `</think>\n\n` are unchanged.
2. **Label and frame (PASS).** I parsed the question with my own regex. On every row its label and frame equal `pointing.label`/`pointing.frame` and the Locate line. All 8,758 null rows say "it is not visible in that frame"; none of the 16,262 point rows do. `pointing.kind`, `selected.uv` and the answer agree on every row.
3. **Digits (PASS).** Think blocks hold only the frame index plus label digits, and no answer coordinate. Label-digit rows: 13990, 14027 (`rj45 outlet`); 20416, 21520, 21911, 24098, 24544 (`3d printer`). The word "first" appears inside labels at 9659, 9677 (`first aid kit`) and 23712, 23823 (`first aid cabinet`).
4. **Tree gates (PASS 25,020/25,020).** I ran `Rows.row`, `r2_contract.validate`/`perception`, `r1_training.row_check`, `row_text_audit.check`, the r0 reserve check and `single_image_row`. The encoder did NOT run: no Qwen3.5 tokenizer exists on local `/scratch` (the snapshot is on `/data2`), and the RGB frames are on `/data2`. The packet did not run it either.
5. **PIN_CHANGE.md is partly correct.** These claims check out: stream identity equals the database SHA (`r1_handover.py:84-85`), `store_hashes.pointing`, the `streams.pointing` pin, the staging entries, the relocator (`launch_r2/build.py:88`) and the 32-row quota. Its gaps are MUST 1, 3 and 4.
6. **Wrong lessons.** No row pairs a not-visible line with a point or a plain Locate line with null. The remaining problems are MUST 2–3 and SHOULD 1–2.

## MUST
1. **The R1 admission erases the Locate line.** `launch_r1/entry.py:189-191` calls `s1_admission.admit(prepare_only=True)`. Its prepare phase always runs (`s1_admission.py:245`) and rebuilds pointing through `build_stream(..., ground_target_filter=True, source_receipt=True)` (`:186-192`). `build_stream` then writes `READOUT_TARGET + mask JSON` (`carrier_c1_data.py:653`), so every target reverts to an empty think. After that, `bind_target` (`s1_admission.py:222-223`) silently replaces `store_hashes.pointing` d5362229.
   The derived receipt cannot avoid this. Admission requires `ground_target_filter=True` (`s1_admission.py:160`), and `carrier_c1_run.py:543-547` refuses a pointing receipt that lacks `target_filter`. PIN_CHANGE calls the rebuild conditional ("If N's preparation invokes build_stream"); it is unconditional.
   Fix: make `build_stream` emit the Locate target after `mask_target`, using the rule in `pointing_locate.py:61-72`. Assert it in the prepared store, and get the one independent review that this admission change needs.
2. **The pointing eval now differs from training.** `evalpath/pointing_markers.py` uses this exact question template. It pins `enable_thinking=False` and `max_new_tokens=64` (`:28`, `:42`) and pre-fills `<think>\n\n</think>\n\n` (`:164-166`); its comment at `:190` reads "The trainer labels start at the JSON answer."
   After this change, no pointing training row has an empty think. The eval therefore conditions on a prefix the student never trains on, and it never exercises the Locate line. Decide between two options: switch to thinking-on as a reviewed scoring change (the longest target, row 3315, is about 32 tokens and fits in 64), or record the mismatch.
3. **`pointing_weights` now weights a copied token.** In the final-mode configs (`configs/E2E-1C.json`, `E2E-1G.json`: decision 5, row_mean 2), `pointing_token_weights` (`carrier_c1_data.py:20-40`) gives the extra weight to the first token after `"point_2d":`. The visible-or-null choice now happens earlier, at `.` versus `:` after "frame k", and that token gets weight of about 1.8. The ` [` or ` null` token that keeps the 5x weight simply follows from the think line.
   My token probe shows the Locate line takes about 28% of the row weight on point rows and about 50% on null rows. Move the decision weight to the Locate decision token, or record the change.
4. **PIN_CHANGE omits launch gates that the new pin trips.** These need to be added:
   - the host receipt's `config_identity` and `loader_audit` (`launch_r1/entry.py:89-94`);
   - an independent review with verdict PASS bound to `identity(cfg)` (`:90`, `:103-104`);
   - a rebuilt `r2_sampling` population and `row_plan_sha256` (`:85-88`).
5. **Run the trainer encoder on CPU before GPUs (AGENTS.md first-batch rule).** Use `training_text` + `encode_frames` with the real Qwen3.5 processor on rows 3 (visible), 0 (null), 13990 (label digits) and 3315 (longest target). Check that the supervised suffix starts after `<think>\n`, that the labels cover the Locate line, and that no tokens merge across the prompt/answer boundary.

## SHOULD
1. **Hyponym absences** (inherited from the source ground truth; the Locate line now states them in words). In each pair, an absent row and a point row share the scene and frame:
   - 1030 `chair` vs 1029 `sofa chair`; 22302 `chair` vs 23912 `office chair`;
   - 7631 `table` vs 7677 `coffee table`; 23829 `table` vs 22727 `coffee table`;
   - 11052 `cabinet` vs 11111 `storage cabinet`; 16527 `cabinet` vs 16585 `storage cabinet`;
   - 11638/11681 and 19033/22348 (`window` vs `window frame`).
   This is a lower bound, because a conflict shows only when the visible label has its own row in that frame. Filter such absences in the next ground-truth rebuild.
2. **Plural labels.** 481 null rows with plural labels read "it is not visible", for example 1220 `clothes`, 963 `blinds` and 275 `shoes`. Number-neutral wording would avoid this if the ruling allows it.
3. **Trinity paths in the staged receipt.** `receipt_pointing_locate_staged.json` keeps Trinity absolute paths in `source_receipt` and in all 57 `inputs`, including the words `student`, `trace` and `geometry`, which `launch_r2/build.py:19-21` forbids in plaintext kit JSON. The old receipt held only deployment paths. Strip these fields before upload, or ship the file as a capsule.

Note: `segment_tags` (logging only) now counts the frame digits as `pointing_coord`. The staged receipt and `TRANSFORM.json` contain none of the words split, revsi, vsibench, distill or qgen.
