# Refute review of the rebuilt tool-contract patches (lane review_contracts, Devin Opus high, trinity-1-3)

**Verdict (r1 packet): ACCEPT AFTER FIXES. The heading part of r1 (HIGH-1, MEDIUM-3) is superseded by the r2 packet, which the section "r2 packet" at the end reviews. Verdict for r2: ACCEPT AFTER FIXES. HIGH-2, MEDIUM-4 and MEDIUM-5 remain open in r2.**

r1 detail: The guard is the reviewed one, the patches apply cleanly, and epoch OFF reproduces the sealed responses byte for byte. Two defects need fixing before tree_rebuild integrates the patches, plus three medium ones and the untested lines. The first HIGH defect means the patches serve distance on near-nadir captures without the training rows ever demonstrating it. The second crashes a row generator in both epochs.

Packet reviewed: `/scratch/jjyeung/orch_n30/contracts_rebuild/out/` (PATCH_geometry 5194976d, PATCH_candidates e58cf3ba, PATCH_box 92c0451e, PATCH_geometry_on_tree_r1 b5039761). My work, scripts and outputs: `/scratch/jjyeung/orch_n30/review_contracts/work/` (scripts in `mytests/`). Line numbers refer to the patched tree. I wrote `work/STEP1_EXPECTATIONS.md` from the records before I opened the builder's report.

## Confirmed
- **Base and application.** Base seal b01ce449: I recomputed it from the 792-file manifest (compact sorted JSON of path→sha256), and every file verifies. All three diffs apply to a fresh base copy with `patch -F0`, with no fuzz, offset or reject, and all 29 patched hashes equal the manifest. tree_r1 (fab2eea8, 807 files) takes `PATCH_geometry_on_tree_r1` + candidates + box cleanly, and the result equals the packet script's output byte for byte. The script refuses a second application.
- **Guard identity.** `validate_up_convention` equals the reviewed text in AST and in source text. My reference copy matches the recovered gravity_guard.py (a62e3975) on all 125 lines.
- **Builder suite.** 82/82 pass on my patched base and on my patched tree_r1. The suite cannot collect on the unpatched base (4 errors), so it does exercise the patches.
- **OFF parity.** I built 360 of my own fixtures: 2 storage orientations × 9 poses (level, pitch −60/+40/−70/−75/−85/+80, roll 45/−80) × small/normal masks × policy/no-policy × 5 name sets (singular, plural, alias, case, "glasses/shelves"), with 17 calls each. The base tree and patched OFF gave identical responses on all 6,120 (`OFFP_base.json` and `OFFP_off.json`). Caveat: on this fixture, head calls raise AttributeError in both trees (no heads), so head-call parity is shown only by the builder's 4 head fixtures.
- **Real rows.** I reran the audit on POOL eb3429c5. 13,001 distance and 1,083 room rows pass it, in both admitted and packed form. My independent check compares the question parser against the generator's own `roles` on the 13,001 admitted distance rows. The two sets are equal on every row, and every row's ground calls name exactly those roles (`REAL_AUDIT_REVIEW.json`).
- **Inherited tests.** I ran the builder's inherited subset (55 test files, 356 cases) on the base tree and on the patched tree with the default ON. The outcomes are identical case by case: 259 pass, 47 fail and 34 error in both trees, all from missing external fixtures (`work/logs/sub_*.xml`).
- **Box bridge.** `bridge_cut` runs only when `contract_epoch` is set and the instance is marked `depth_cut_applied`. Replay reads the recorded per-instance marker. With epoch ON, every policy-path fixture changes from `box unavailable` to a served distance (`OFFP_on.json`).

## Findings
**HIGH-1. Training and runtime handle `heading unavailable` in opposite ways, so the restored near-nadir distances are never trained.** On a near-nadir capture, the runtime answers `<ground … mode="box">` with `chair: heading unavailable\nsize …` and then serves `<gap>` (`distance 0.90 m`, `distance 2.10 m`; `NADIR_FLOW.json`). The training side treats that response as a failure in three places:
- `response_status` returns `heading unavailable`.
- `training_contract.py:95` marks the ground failed, and `:82` then defers the very row the runtime serves as `contract_call_after_failed_ground`. Failing input: ground chair → `chair: heading unavailable\nsize 0.43 x 0.06 x 0.86 m`, then gap → `distance 0.90 m`. `attack_nadir_flow.py` prints `['contract_call_after_failed_ground']`.
- The program renderers stop before the gap: `generator/derivgen_v7/derivgen/box_v313.py:335,473` and `trace_format/box_v313.py:390,617`. They write "The box for X is heading unavailable, so I estimate from the frames."

As a result, GT training rows on near-nadir captures turn from distance programs into recovery rows. The record puts at least 8 of 51 sampled d3 references within 10° of nadir, and the threshold covers 17.5°. The 21 dev-S1 items would recover only if the model calls a tool that its training teaches it to abandon. The fix is to treat a metric-only response as usable for gaps in the audit, the programs and `response_status`. One way is to give it a status other than failure and let the gap follow. Add a test that admits ground→heading unavailable→gap.

**HIGH-2. The generator dispatch turns classes into functions in both epochs and breaks subclassing.** `derivgen/ground_v313.py:513-517` and `derivgen/box_v313.py` (end of file) rebind `Session`, `GTInstances`, `BoxRegistry` and the providers to plain functions at import time. `generator/ground_rows_out/render_gaps_v314.py:16` declares `class Provider(I.GTInstances)`, so `instance_provider(clip)` raises `TypeError: function() argument 'code' must be code, not str` in the patched tree. The base tree builds the class (reproduced on both trees). `render_full.py` imports this module, so count-type scene rows cannot be generated, even with contract_epoch OFF. The OFF byte-identity claim therefore does not hold for the generator. The dispatch is also untested: mutation M15 (drop the BoxRegistry dispatch) survives. No proof regenerates any training row under ON and compares it with the sealed rows, although the runtime Session/BoxRegistry differ from the generator's copies by 60 and 210 diff lines (provider defaults, `form_requires_*` refusals, gap operands). The fix is to dispatch through a class factory or subclass that stays a class, and to add a test that regenerates rows from fixtures under ON and OFF.

**MEDIUM-3. The head-call heading policy checks frame 1, but these calls depend on the frames they name.** `carrier_c1_decode.py:218-228` refuses `<move>`, `<turn>`, `<pose>`, `<depth_at>` and `<angle>` whenever frame 1's in-plane up is below 0.3. `DECODE_ATTACK.json` adds 3° of gravity noise in four directions and shows:
- (A) With frame 1 at −88° and frames 2-3 upright: `pose 2` yaw swings 20/−36/−160/76°, so refusing it is right. `move 2→3` and `turn 2→3` stay identical (+0.15/+0.11 m, +20°) yet are refused. The cause is algebraic: `level_R_L1(i).T @ to_l1` cancels frame 1. This over-refuses camera direction and rotation items.
- (B) With frame 1 upright and frame 2 at −88°: `turn 2→3` swings +40/−16/−140/+96° and `move 2→3` dx/dz rotates, yet both are served. This under-refusal is pre-existing but contradicts the claim that "heading outputs are well defined or refused". Real d3 captures have near-nadir later frames, for example frame 31 at −87.3°.

The fix is to gate each call on the frames it uses: move(i,j) on frame i; turn(i,j) on i and j; pose(k) and depth_at's f1 coordinates on frames 1 and k. Separately, the `<move>` fallback distance is untested: mutation M10, which takes the distance from frame 1 instead of frame i, survives.

**MEDIUM-4. The admission-versus-runtime check is mostly a tautology, and the two candidate sources can disagree in deployment.** In `real_audit_b2.py`, admission (`admission_phrases`) and runtime (`build_backend`→`candidate_names`) both call `phrases.candidate_phrases(question, options, None)` on the same input. The report's word "independently" is wrong, and only the membership lookup is a second code path. In deployment, when the source has a mask cache, the runtime universe is every cache phrase (`ground_v3.py:74-75`, `phrases.py:50`). Without a manifest, admission uses the question parser. So a row can be admitted whose operand the cache-universe runtime refuses, whenever the cache lacks the question's phrase. The runtime then prints an operator fault that training excludes. The cache wiring has no test: M13 (universe from `source.names`) and M17 (`cache_phrases` → None) both survive. The fix is to require a `candidate_manifest` of cache phrases for admission whenever the reader uses caches, or to make one function produce both sets from the same inputs. Add tests that kill M13 and M17.

**MEDIUM-5. `response_status` reports a served point ground as failed.** `contracts.py:37-43` returns `size unavailable` for a seen object whose size is missing (`ground_lifting.py:189` prints that line after a valid point). The audit then defers the row. Failing input: `<ground obj="chair">` → `chair: frames 2,3 (best 2)\nP1: …\nsize unavailable`, then grounds of table and lamp. The verdict is `['contract_call_after_failed_ground']`; with a size present it is `[None]`. The renderers break at the same place. The fix is to count only name-bound statuses on the first line (`name: status`) or the bare status bodies.

**LOW-6.** `audit_training_contract` raises AttributeError on a call token of None or a non-dict `routing` (100 of 100 corrupted real rows), and the materializer catches only `ValueError/KeyError/TypeError` (`s1_routing.py:342,372,413`). Deferrals record counts per reason, not the qid.

**LOW-7.** `normalize_phrase` maps glasses→glasse, mattresses→mattresse, buses→buse, knives→knive and lens→len, so `annotation_labels` no longer matches the labels "glass" and "mattress". `cache_key` raises `duplicate_normalized_cache_phrase` when a cache holds both "chair" and "chairs". A question containing `"` raises `invalid_object_name` inside `candidate_phrases`, which crashes `build_backend`. The parser returns (back, left, right) for a relative-direction question and () for an absolute-size question; neither type is routed.

**LOW-8.** The audit defers every `error:` response as an operator fault, which covers model-caused call errors too. That is broader than ruling 2.4(d). The heading check also runs before calculator dispatch, so `<angle>` and `<turn from=P at=P to=P>` are refused as heading unavailable. With a read-only target, which sealed trees are, the apply script fails at `mv -T` (`apply_contract_patches.sh:40`) after validation. The target stays intact, but the script leaves a `.contracts-*` staging copy beside it.

**LOW-9.** The claim "11/11 rolled pass" rests on floating-point noise: −R[2,1] = cos 90° ≈ 6e-17. Rolls of ±91° are refused, and so is a near-nadir frame 1 whose other frames are rolled 90.5°. This matches the sealed guard and is not a defect, but it does not show that rolled captures are served.

## Pose attack (`GUARD_ATTACK.json`; my own c2w construction, 32 frames)
In my construction, "−88°" looks up and "+88°" looks down. The guard depends only on plane and margin, and a true-nadir rerun gives the same four verdicts: upright rest serve, sign-flipped serve, rest inverted refuse, rest rolled 90.5° refuse. The −88° rows below therefore stand for near-vertical captures in either direction.
| Pose | Plane / margin | Sealed | Patched ON | Heading |
|---|---|---|---|---|
| Upright, landscape or portrait storage | 1.0 / 1.0 | serve | serve | defined |
| Roll ±89° / ±90° / ±91° / 179-180° | 1.0 / ±.017, 0, −1 | serve, serve, refuse, refuse | same | defined |
| Pitch −72.0 / −72.54 (plane 0.300) | .309 / .300 | serve | serve (sign test) | defined |
| Pitch −72.55 / −73.0, rest upright | .2999 / .292 | serve | serve (median) | **unavailable** |
| Same, every frame inverted | margin < 0 | refuse | refuse | – |
| −88°, rest upright | .035 / .035 | serve | serve | unavailable |
| −88° with frame-1 sign flipped, rest upright; 41069053-like (−88.2°, margin −.020) | .031-.035 / <0 | **refuse** | **serve** | unavailable |
| −88°, rest inverted / rest rolled 90.5° / 15 up and 16 inverted | .035 / .035 | **serve** | **refuse** | – |
| Zenith +88°, rest upright / rest inverted | .035 | serve / serve | serve / **refuse** | unavailable |
| All frames near nadir, upright or inverted | .017 | serve / refuse | serve / serve (inversion undetectable) | unavailable |
| Non-orthonormal (2R, shear, NaN) | – | – | contract refuses `camera_rotation_not_proper` or `missing_or_invalid_K_transform` first | – |

Wherever the heading is unavailable, the patched runtime serves box size, gap and camera-gap distance, room area, instance count and the `<move>` distance. It refuses f1 centres, yaw, points, instances' points, witness points, keypoints, pose, turn, the move direction and depth_at. Calling `validate_up_convention` directly on NaN or scaled input would serve it, but no caller does so without the contract's own checks running first.

## Behaviour changes with contract_epoch ON (`OFFP_on.json`; 1,988 of 6,120 responses changed)
1. **Guard.** Near-nadir references whose frame-1 sign is wrong now serve; these are the record's 12 proxy captures and 21 items. References with plane < 0.3 whose usable frames have a negative median now refuse where the sealed guard served (table rows marked **refuse**).
2. **Heading unavailable** at plane < 0.3 replaces f1 centres, yaw, points and head outputs. This covers the record's 2 near-nadir proxy captures that the sealed guard already served: their distances stay served and their heading-dependent outputs become refused.
3. **Names are normalized and singularized** before reaching the mask provider and cache. Plural calls ("chairs") now resolve to the "chair" source, which changed boxes and distances on every pose of my plural fixture.
4. **The candidate universe** becomes open-vocabulary: cache phrases, or the question parser when there is no cache.
5. **The MDG/policy bridge** serves boxes that were `box unavailable` on every pose.
6. **Training rows** come from the runtime Session, BoxRegistry and providers instead of the generator's copies (HIGH-2). `category_vocab.normalized` changes for GTInstances pooling.
7. **The audit defers rows** with operator faults, `error:`, missing responses, outside operands, calls after a failed ground, or a recovery without an answer.

## Mutations (builder suite, 82 tests; `MUTATION_RESULTS*.json`): 13 of 18 killed
Killed: M1 guard `>=`→`>`; M2 median threshold; M3 `down[:2]`→`down[1:]`; M4 drop the `error:` status; M5 drop bare `unavailable`; M7 drop the operator-fault check; M8 ungate `bridge_cut`; M9 drop the ies→y rule; M11 camera-gap centre from frame 1; M12 skip the materializer deferral; M14 witness gaps without the heading check; M16 drop the routing heading branch; M18 print instance points when the heading is unavailable.
**Survived:** M6 allow a gap after a failed ground, which is the core recovery rule; M10 `<move>` fallback distance from frame 1; M13 universe from `source.names`; M15 drop the generator BoxRegistry dispatch; M17 drop `cache_phrases` wiring in `build_backend`. The builder's "204/204, 248/248, 9/9 executed" coverage counts executed lines, not asserted ones.

## Builder claims I could not confirm
- That the real near-nadir capture replay serves end to end: it is pending (build3, geometry_8c58df15). I did not run it, and the 12/21 figure remains a records projection.
- "Admission independently derives its set": false, see MEDIUM-4.
- That training and serving share one formatter safely: not shown (HIGH-2, M15).
- tree_r1 suite "16 vs 15" failures: I did not rerun the tree_r1 suite. On the sealed base, the inherited subset gives the same outcomes before and after the patches.

## What I did not check
- Model-side effects and GPU paths, and the head-gravity versus G3T threshold disagreement on real captures.
- Real SAM3 caches, which would show whether duplicate singular/plural phrases occur.
- The evaluation reader port, and Orchard.
- ContextVar inheritance in thread pools: new threads see the default ON, but none of the touched serving paths spawn threads.

## r2 packet (`out/*_r2*`, HEADING_DEPENDENCE_R2.md; reviewed for its heading part as the 2049Z note asks)
- **Application and suite.** PATCH_{geometry,candidates,box}_r2 apply with zero fuzz to base b01ce449 (32 files, all hashes equal PATCH_MANIFEST_R2), and the r1 rebase applies to tree_r1. The r2 suite (tests_r2) passes 108/108 on both trees.
- **The 41-capture question, judged on r1.** r1 withheld heading-free outputs on every capture with plane < 0.3: `<move i j>` dx/dz, `<turn i j>`, depth_at camera coordinates and f1 vertical, and pose f1 vertical. Distance, area, size and count were served. r1 never served a heading-dependent field from the frame-1 basis. It did serve move/turn/pose yaw for a degenerate frame i while frame 1 was defined (MEDIUM-3 B).
- **r2 heading policy, attacked with my own rotated copies.**
  - Frame-1 basis rotated about gravity (`R2_YAW.json`): frame 1 near vertical, yawed 0/40/130/250°. Every served field is byte-identical: box frames, f1 vertical, sizes, all gaps and camera gaps, point camera coordinates, instances, `move 2→5`, `turn 2→5`, `turn 6→7`, and depth_at camera coordinates. The two exceptions are room area ±0.01, because frame 1's own floor points move, and one `move 6→7` distance at a rounding boundary.
  - 3° gravity error in four directions (`R2_INVARIANCE.json`): served fields move only by the physical tilt effect (f1 vertical ±0.11 m at 2 m, gap ±0.04 m). Sizes are identical across directions, and frame 1 upright shows the same pattern.
  - Refused fields are exactly those that rotate with the basis: f1 horizontal x/z, pose yaw relative to frame 1, `move 1→j` dx/dz, `turn 1→j`. A degenerate frame i (frame 6 near vertical with frame 1 upright) now refuses `move 6→7` dx/dz, `turn 6→7` and pose 6 yaw, while it serves pose 6 f1 centre and depth_at frame 6 f1. Those last two depend only on the defined frame-1 basis and frame 6's full rotation. Calculator angle and turn keep the dot product and category and hide u and v; both are invariant under rotation about gravity.
  - Conclusion: in r2 no served field depends on an undefined heading, and every withheld field does. **MEDIUM-3 is closed.**
- **HIGH-1 is closed in r2.** The programs gate on the registry state (`box_v313.py` renderers), and the audit treats a partial ground (`name: frames …` carrying "heading unavailable") as served. My near-nadir flow (ground, ground, gap) now gets audit verdict `[None]` (`NADIR_FLOW_R2.json`).
- **Still open in r2:**
  - HIGH-2: `render_gaps_v314.instance_provider` raises the same TypeError.
  - MEDIUM-4: the tautological universe check and cache-versus-parser sources are unchanged.
  - MEDIUM-5: a point ground with "size unavailable" still gets `contract_call_after_failed_ground`.
  - LOW-6 to LOW-8.
- **r2 mutations (108-test suite; `R2_MUTATION_RESULTS_*.json`).** Killed: R1 (move gated on frame 1 instead of frame i), R2 (turn never refused), R4 (partial ground counted as failed), R5 (renderer back to response_status), R6 (yaw of a degenerate frame k served). Survived: M6, M13, M15, M17 (unchanged from r1), and **R3**: dropping the clause in `response_status` that maps partial-heading lines to `heading unavailable` fails no test.
- **Fixes required before integrating r2** (patched-r2 tree lines):
  1. HIGH-2, at `derivgen/ground_v313.py:513-517` and `derivgen/box_v313.py:567+`. Failing input: `render_gaps_v314.instance_provider(clip)` raises `TypeError: function() argument 'code' must be code, not str` with contract_epoch ON or OFF. It matters because count-type scene rows cannot be generated and the generator is not byte-identical in OFF. Keep classes as classes (a factory with `__new__` dispatch or a subclass) and add a row-regeneration test under ON and OFF that kills M15.
  2. MEDIUM-5, at `trace_format/contracts.py:57`. Failing input: point ground `chair: frames 2,3 (best 2)\nP1: …\nsize unavailable` followed by two grounds gives `contract_call_after_failed_ground`. It matters because a served ground counts as failed and the training row is deferred. Count only name-bound statuses.
  3. MEDIUM-4, at `ground_v3.py:75` and `training_contract.py` (`admission_phrases`). With a mask cache the runtime universe is the cache phrases, while admission without a manifest uses the parser, so an admitted operand can be refused at runtime with an operator fault. Require the cache manifest for admission when caches deploy, and add tests that kill M13 and M17.
  4. Add tests that kill M6 (a gap after a failed ground must defer) and R3 (partial-heading lines map to `heading unavailable`).
- **New in r2, LOW.** Training rows for head tools still replay recorded GT values (`carrier_c1_routing.py`, `recorded` branch), so no camera training row shows the `heading unavailable (frame k)` or partial-f1 formats the runtime now prints. `p3_printed_calculator.py` becomes an alias module, so any receipt that hashes that file's bytes changes.
