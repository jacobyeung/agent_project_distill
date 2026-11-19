GO AFTER FIXES. MUST: (M1) refuse or authenticate `r1_training.camera_trace_form` when the routing stream is deferred, since production then never composes.

Reviewer: changed-files review of PATCH_CAMFORM 2167d5d9 over base 57a1f14d + PATCH_A b95c1c61. All checks ran on my own trees and scripts in `work/` (results in `work/S3_VERIFY.json`, `S4_POLICY.json`, `S7_DECLARATION.json`).

## MUST
M1. With `routing_slices='deferred_first_boundary'`, a set `camera_trace_form` is silently ignored and its pin is never checked.
- Native admission composes only when `deferred(cfg)` is false (`student_pilot/s1_admission.py:214-216`), and `deferred` is true whenever `routing_slices` is present (`student_pilot/r1_coverage.py:67`). `launch_r1/production_proof.py:139` and `launch_r1/build.py:100-103` drop the compose step in that mode.
- `r1_routing.py:63-65` is the only reader of the field. `work/s8_deferred_noop.log` shows `deferred()` returning True with `camera_trace_form='not-a-pin'`: no rewrite, no receipt entry, and the malformed pin is accepted, which breaks requirement 6 on that path.
- The patch's composition evidence (`camform/code/compose_extract.py:34`) and unit tests (`tests/test_r1_camera_trace_form.py:94,103,108`) use exactly this mode, which production never composes.
- Fix: raise (for example `R1_CAMERA_TRACE_FORM_REQUIRES_COMPOSITION`) when the field is set and `deferred(cfg)` is true, at config validation or before `s1_admission.py:214`, and add a test.
- My production-shaped rerun (declaration mode, `camera_wording` bound to the real e8cbda99 rows) behaves like the deferred harness, so the extract evidence otherwise carries over.

## SHOULD
S1. The policy check compares JSON content, not bytes (`r1_camera_trace_form.py:64`). A reformatted or key-reordered policy with a matching pin (sha c97c3ad2…) is accepted. If 169c439a is meant to be the only valid policy, compare `pin['sha256']` to that constant.
S2. The receipt counts rewritten rows per type and per rule, not changed lines (`r1_camera_trace_form.py:71-90`). On all 8,172 rewritten rows I checked, each row has exactly one changed line, so the counts agree. A row with two matching events would make them differ.

## Verified (no problem found)
1. The base tree verifies 939/939 against seal 57a1f14d. PATCH_A, then PATCH_CAMFORM, apply with fuzz 0. Base+PATCH_A seals to 290e2119. The four touched files match FILES_TOUCHED.json hashes, nothing else differs, and the result equals camform `work/new`.
2. With the field absent, rows.sqlite, membership.json and receipt.json are byte-identical to base+PATCH_A at the same output path. This holds on the 6,000-row extract (63002301 / fea45e58 / 5e1e1095), on an 11,081-row mixed base, and in declaration mode.
3. With the field present, every composed row was diffed against base+PATCH_A. Only `/target`, plan/canonical_text `events[k].text` and span start/end change; there are 0 other-path violations.
- Extract: 2,000 rotation rows change one line each under CAM-ROT-WORDS-v1, and 1,996 direction rows change one line each under CAM-DIR-SYMBOL-v1. Unchanged: 2,000 displacement rows and 4 direction rows that have no negated option.
- camera_B rows: 1,698 rotation and 1,678 direction rows change; 3 direction rows stay unchanged.
- Calls, response events and values, answer, gt_answer, gt_pose9, gt_up, qid, question, options, frames and the parallel target column are identical.
- Offsets: all 7,372 changed rows re-render to the stored target, and their spans equal `render()` and slice identical `<tool_response>` bytes. No tokenizer is available offline, so this check is character-level; span edges are `<tool_response>` special tokens.
- My own rule implementation reproduces every rewrite (0 mismatches), and no old form remains.
4. Counterparts: all 5,979 matched rows (displacement 1,994, rotation 1,993, direction 1,992) have identical target, event texts, spans and answers in `fbp_cam` rows e8cbda99. This includes a seeded 300-row sample.
- The 21 rows without a counterpart have no residual old form and pass the shared grammar with 0 errors. After the rewrite, 6,000/6,000 rows pass the grammar.
- In declaration mode, all 1,196 base/slice pairs share one target when the field is enabled, against 397 (displacement only) when absent. All 1,196 slice rows stay unchanged.
5. No non-camera row changes. The 4,000 relative_count rows and all displacement rows are unchanged. The reader refuses the same 2,000 absolute-distance rows in both runs (`EXTENT_RECEIPT_REQUIRED`).
6. The pin refuses 17 malformed or changed cases: None, False, {}, a string, a list, an extra key, a missing sha, a wrong sha, a relative path, a missing file, stale bytes, reordered rules, an extra rule, a changed input hash, an extra field, a duplicate key, plus a bad pin through compose (no output dir created). The only gaps are M1 and S1.
7. The receipt records the policy pin, rule ids, implementation sha 8dff7733, the base DB pin and counts by type and rule. Rows refused by Filters or by the reader are not counted.
8. Filters judge the unrewritten row: the digests Filters saw match the source rows (6,000/6,000 and 11,081/11,081).
- The predicates key on qid, scene, source, canonical and scene strings (`r1_routing.py:35-52`, `row_removals.py:9-15`, `carrier_c1_run.py:340-385`). A constant phrase swap or a deletion cannot alter them.
- Reader checks run on the rewritten row (`r1_routing.py:106-112`). The mocks hide no rule break; the one production path that skips composition is M1.
- The faithful `materialize` path would refuse the rewritten direction lines (`generator/derivgen_v7/derivgen/materialize.py:472,561`), but R1 refuses own-value and faithful rows (`r1_training.py:81,83`).
- `rewrite_row` raises outside the reader's try block, so a non-re-rendering camera row would abort the whole composition (fail-closed). None of the 11,081 camera rows I tested does this.
9. Shortcuts: none found.
- The rotation edit is one constant sentence, and rotation rows have no options (2,000/2,000).
- In direction rows a number is hidden exactly when the option label is negated: all 794 hidden winners are negated labels and all 1,206 shown winners are positive. The question's options already fix that, independent of the answer.
- Answer letters are balanced (A 534, B 488, C 476, D 502). The rewrite only deletes text, so it adds no answer information.

## Suites
- `tests/test_r1_camera_trace_form.py` passes 9/9, and `tests/test_r1_subset` passes 11/11 on both trees.
- `test_r1_build13/16/17` error identically on both trees from pre-existing causes: the `R2_PROOFS` env var is unset and `fixtures/work/build6/INIT_INPUT.json` is missing. These do not block.

Scripts: `work/s1_apply.py`, `s2_build.py`, `s2b_build_mixed2.py`, `s2_compose.py`, `s3_verify.py`, `s4_policy.py`, `s7_declaration.py`. The partial `work/compose/mixed_same/` comes from the first mixed run, which hit the 200 MB local composition limit; I left it in place.
