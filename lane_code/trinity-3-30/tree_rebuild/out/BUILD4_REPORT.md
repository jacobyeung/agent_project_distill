# Build 4 report

**NOT READY.** The tree and kits contain tested intake and admission repairs, but the exact runtime staging proof, durable full-state recovery qualification, vocabulary witness, complete package pass and zero-gap CPU coverage are not established. No launch, remote call or GPU work was performed.

The disposition identifiers below refer to `work/review1/REVIEW_VERDICT_TREE.md` and the build request. “FIXED” describes the named behavior, not production readiness.

| Review item | Disposition | Implementation | Evidence / remaining work |
|---|---|---|---|
| 1 | PARTIAL | work/tree_r1/launch_r2/staging.py:147 | Pinned runtime and sandbox command implemented; production verification runs before staging. Actual venv/bwrap bytes are absent from named inputs, so neither Python-without-numpy entry proof nor Python 3.6 execution is established. Syntax-only evidence: `work/build4/KIT_CHECKS.json`. |
| 2 | PARTIAL | work/tree_r1/launch_r2/plan.py:9 | Every relative config path has a staging entry, and the walker refuses gaps. Tiny assembly/hash/escape tests pass. Actual parent archives and nested native path layout remain unverified; a staging-list entry is not a physical staging proof. `work/build4/KIT_CHECKS.json`; `tests.test_r2_build4`. |
| 3 | PARTIAL | work/tree_r1/student_pilot/r2_adapters.py:7 | Published nested questions, ground_record events and raw printed pool events use the masked reader; the envelope pins the shared contract. Recovery prose, converted units and sealed simulated misses pass. Per-row refusals retain denominators. Required slice results are below. Full-store final sampler reindexing after a late frame/materialization refusal remains unproved. |
| 4 | PARTIAL | work/tree_r1/launch_r2/persistence.py:22 | Milestone/checkpoint callbacks archive and verify locally, upload through the pinned parent writer, then permit project mirroring. Signal handler requests stop through a local file. The fake uploader proves archive/range receipts survive project ENOSPC. Retained checkpoint archive copies are not yet folded into the native whole-leg disk budget. Real checkpoint restore, remote sessions, deadline/memory admission and durable manifest recovery remain unqualified. `work/build4/tests_quick_final/PERSISTENCE.json`. |
| 5 | FIXED; DELIVERY BLOCKED | work/tree_r1/student_pilot/r2_policy.py:94 | Gateway requires a verified kit; file/item membership and choices come from its bound config. Reviewer relabel/omitted-selector probes refuse. Delivered catalog is empty because real bank bytes were not supplied; no evaluation is admitted. `work/build4/review_current/PROBE_BANK.json`; `tests.test_r2_policy`. |
| 6 | FIXED | work/tree_r1/student_pilot/r2_contract.py:184 | GT mask and geometry provenance are mandatory; selector authority refuses. Published-row mutations refuse. `work/build4/review_current/MUTATIONS.json`; `tests.test_r2_build4`. |
| 7 | FIXED | work/tree_r1/launch_r2/parent.py:16 | Real parent records pass through configure(overrides=False); garbage parents refuse. Parent metadata is in fixtures. `tests.test_r2_build4.ReviewGuards.test_parent_configuration_path`; `tests.test_r2_build3`. |
| 8 | FIXED | work/tree_r1/student_pilot/r2_scene_bindings.py:38 | Merged bytes bind config, totals, census and pool upstream. Prior derivation is only an equivalence test. `tests.test_r2_build3b`; `student_pilot/r2_dev_merged.json` has the requested digest. |
| 9 | PARTIAL | work/tree_r1/student_pilot/r2_openers.py:11 | Keep now refuses missing witness, wrong lineage or non-full LM at preparation, and never resets silently. Actual vocabulary witness remains absent; delivered config explicitly binds null and cannot prepare. `tests.test_r2_build4`; `tests.test_r2_build3`. |
| 10 | FIXED | work/tree_r1/launch_r2/bootstrap.py:57 | Both production bootstrap levels invoke native ANON_OK/status/hits/commit checks. Builder verification alone retains build-only mode. `work/build4/KIT_CHECKS.json`; `tests.test_r2_build`. |
| 11 | PARTIAL | work/tree_r1/launch_r2/build.py:61 | Metadata/disclosure capsules, local source extraction, opaque shell variables and hashed refusal/log records are implemented. Scanner covers output paths, all JSON-looking files and every uncapsulated field, with no output-path exceptions. Both staged kits scan clean. Native runtime output surfaces after full host execution remain unqualified. |
| 12 | FIXED | work/tree_r1/launch_r2/build.py:260 | Each kit carries its own unsigned GO=false authorization and bound config digest. No parent conditions authorize this leg. `work/build4/KIT_CHECKS.json`. |
| 13 | FIXED | work/tree_r1/launch_r2/host.py:225 | Host checks packet/config bytes against the kit; entry checks the bound original and prepared config digest. Derived store-path changes are separately hashed. `tests.test_r2_build3_gaps`. |
| 14 | FIXED | work/tree_r1/student_pilot/r2_exclusions.py:42 | Conservative eval_rooms exclusion remains active for every VQA family. Card and repeat table list its observed slice removals. Production repeats remain unqualified. `out/BUILD4_REPEAT_TABLE.md`. |
| 15 | FIXED | work/tree_r1/student_pilot/r2_materialize.py:41 | Refusal names both families and keeps the rejected row in its denominator. `tests.test_r2_data_path`. |
| 16 | FIXED | work/tree_r1/student_pilot/carrier_c1_data.py:449 | R2 training and host reader paths require bound sampling; natural-draw fallback refuses. `tests.test_r2_build4.ReviewGuards.test_missing_sampler_refuses`; `tests.test_r2_sampling`. |
| 17 | FIXED FOR REVIEW MUTATIONS | work/tree_r1/tests/test_r2_build4.py:21 | All applicable reviewer statement mutations are killed; removed per-row contract mutation is replaced by envelope/version tests. The mutation harness changes live function code while retaining source pins; each targeted baseline passes. `work/build4/mutation_final/RESULTS.json`; final grammar recheck: `work/build4/mutation_current_grammar/RESULTS.json`. |

## Real rows and causes

The unchanged published slices run through the real normalizer, validator, intake and materializer to the frame-host marker. RGB paths/hashes stand in; no real RGB is read. Coverage envelopes copy published scene identities and do not establish a new independent scene census. Missing source-length fields use the explicit lower bound max(source ordinals)+1 only in this metadata proof. FPS joins use the parent authority and published row metadata, never answers; every join source is recorded in `work/build4/rows_complete/CLOCKS.json`. Source rows remain unchanged. The initial command was `work/build1/REAL_ROW_PROOF.sh work/build4/rows_complete`; `work/build4/replay_materialize.py` reuses its immutable envelopes for the final shared-grammar wrapper.

| Slice / family | Seen | Admitted | Refused | eval_rooms | Production repeats | Evidence |
|---|---:|---:|---:|---:|---|---|
| slices_v3/a0_recovery | 1532 | 1458 | 74 | 74 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/a0_recovery/materialization.json` |
| slices_v3/a0_room | 476 | 431 | 45 | 45 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/a0_room/materialization.json` |
| slices_v3/a0_units | 2000 | 1915 | 85 | 85 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/a0_units/materialization.json` |
| slices_v3/d0_facing_easy | 2000 | 1881 | 119 | 119 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_facing_easy/materialization.json` |
| slices_v3/d0_facing_hard | 2000 | 1866 | 134 | 134 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_facing_hard/materialization.json` |
| slices_v3/d0_facing_medium | 2000 | 1870 | 130 | 130 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_facing_medium/materialization.json` |
| slices_v3/d0_retrace_box_3d | 2000 | 1699 | 301 | 301 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_box_3d/materialization.json` |
| slices_v3/d0_retrace_obj_appearance_order | 2000 | 1709 | 291 | 291 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_obj_appearance_order/materialization.json` |
| slices_v3/d0_retrace_object_counting | 2000 | 1961 | 39 | 39 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_counting/materialization.json` |
| slices_v3/d0_retrace_object_rel_direction_easy | 2000 | 1912 | 88 | 88 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_rel_direction_easy/materialization.json` |
| slices_v3/d0_retrace_object_rel_direction_hard | 2000 | 1897 | 103 | 103 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_rel_direction_hard/materialization.json` |
| slices_v3/d0_retrace_object_rel_direction_medium | 2000 | 1849 | 151 | 151 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_rel_direction_medium/materialization.json` |
| slices_v3/d0_retrace_object_rel_distance | 2000 | 1857 | 143 | 143 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_rel_distance/materialization.json` |
| slices_v3/d0_retrace_object_size_estimation | 2000 | 1994 | 6 | 6 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_retrace_object_size_estimation/materialization.json` |
| slices_v3/d0_route_planning | 2000 | 1913 | 87 | 87 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_route_planning/materialization.json` |
| slices_v3/d0_totals | 1240 | 1192 | 48 | 48 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/d0_totals/materialization.json` |
| slices_v3/pool_abs_distance | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/pool_abs_distance/materialization.json` |
| slices_v3/pool_room | 672 | 0 | 672 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/pool_room/materialization.json` |
| slices_v3/pool_route_planning | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/pool_route_planning/materialization.json` |
| slices_v3/sealed_vqa_box_3d | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_box_3d/materialization.json` |
| slices_v3/sealed_vqa_obj_appearance_order | 2000 | 1265 | 735 | 389 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_obj_appearance_order/materialization.json` |
| slices_v3/sealed_vqa_object_abs_distance | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_abs_distance/materialization.json` |
| slices_v3/sealed_vqa_object_counting | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_counting/materialization.json` |
| slices_v3/sealed_vqa_object_rel_direction_easy | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_direction_easy/materialization.json` |
| slices_v3/sealed_vqa_object_rel_direction_hard | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_direction_hard/materialization.json` |
| slices_v3/sealed_vqa_object_rel_direction_medium | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_direction_medium/materialization.json` |
| slices_v3/sealed_vqa_object_rel_distance | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_distance/materialization.json` |
| slices_v3/sealed_vqa_object_size_estimation | 2000 | 0 | 2000 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_object_size_estimation/materialization.json` |
| slices_v3/sealed_vqa_room_size_estimation | 387 | 0 | 387 | 0 | unqualified: slice only | `work/build4/rows_final_source/slices_v3/sealed_vqa_room_size_estimation/materialization.json` |
| slices_final/a0_pool_abs_distance_reworded | 2000 | 1876 | 124 | 105 | unqualified: slice only | `work/build4/rows_final_source/slices_final/a0_pool_abs_distance_reworded/materialization.json` |
| slices_final/a0_recovery | 1532 | 1458 | 74 | 74 | unqualified: slice only | `work/build4/rows_final_source/slices_final/a0_recovery/materialization.json` |
| slices_final/a0_room | 476 | 431 | 45 | 45 | unqualified: slice only | `work/build4/rows_final_source/slices_final/a0_room/materialization.json` |
| slices_final/a0_units | 2000 | 1915 | 85 | 85 | unqualified: slice only | `work/build4/rows_final_source/slices_final/a0_units/materialization.json` |

Every refusal is listed by QID in its materialization report. Non-exclusion causes:

- `slices_v3/pool_abs_distance`: 769 × `Shared grammar: number_word`; 1222 × `Shared grammar: number_word,number_not_allowed,unit_quantity`; 9 × `needs frame metadata: supply the pinned frame_map join before intake`. Source: `work/build4/rows_final_source/slices_v3/pool_abs_distance/materialization.json`.
- `slices_v3/pool_room`: 672 × `lineage_less_room: missing source-row and frame lineage`. Source: `work/build4/rows_final_source/slices_v3/pool_room/materialization.json`.
- `slices_v3/pool_route_planning`: 2000 × `Shared grammar: line_kind,no_evidence`. Source: `work/build4/rows_final_source/slices_v3/pool_route_planning/materialization.json`.
- `slices_v3/sealed_vqa_box_3d`: 2000 × `Empty think block`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_box_3d/materialization.json`.
- `slices_v3/sealed_vqa_obj_appearance_order`: 82 × `Shared grammar: exhaustive_frames`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_obj_appearance_order/materialization.json`.
- `slices_v3/sealed_vqa_object_abs_distance`: 2000 × `Program-type row offered as direct`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_object_abs_distance/materialization.json`.
- `slices_v3/sealed_vqa_object_counting`: 163 × `Shared grammar: exhaustive_frames`; 1777 × `Shared grammar: exhaustive_frames,number_not_allowed`; 9 × `Shared grammar: exhaustive_frames,number_not_allowed,line_kind`; 2 × `Shared grammar: exhaustive_frames,number_not_allowed,no_evidence`; 48 × `Shared grammar: number_not_allowed`; 1 × `Shared grammar: number_not_allowed,no_evidence`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_object_counting/materialization.json`.
- `slices_v3/sealed_vqa_object_rel_direction_easy`: 1999 × `Shared grammar: angle_or_coordinate,number_not_allowed,unit_quantity`; 1 × `Shared grammar: angle_or_coordinate,number_not_allowed,unit_quantity,line_kind`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_direction_easy/materialization.json`.
- `slices_v3/sealed_vqa_object_rel_direction_hard`: 1997 × `Shared grammar: angle_or_coordinate,number_not_allowed,unit_quantity`; 1 × `Shared grammar: angle_or_coordinate,number_not_allowed,unit_quantity,line_kind`; 2 × `Shared grammar: angle_or_coordinate,number_word,number_not_allowed,unit_quantity,number_word`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_direction_hard/materialization.json`.
- `slices_v3/sealed_vqa_object_rel_direction_medium`: 1999 × `Shared grammar: angle_or_coordinate,number_not_allowed,unit_quantity`; 1 × `Shared grammar: angle_or_coordinate,number_not_allowed,unit_quantity,line_kind`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_direction_medium/materialization.json`.
- `slices_v3/sealed_vqa_object_rel_distance`: 19 × `Shared grammar: frame_range,number_not_allowed,unit_quantity`; 1980 × `Shared grammar: number_not_allowed,unit_quantity`; 1 × `Shared grammar: number_not_allowed,unit_quantity,line_kind`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_object_rel_distance/materialization.json`.
- `slices_v3/sealed_vqa_object_size_estimation`: 1999 × `Shared grammar: number_not_allowed,unit_quantity`; 1 × `Shared grammar: number_not_allowed,unit_quantity,no_evidence`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_object_size_estimation/materialization.json`.
- `slices_v3/sealed_vqa_room_size_estimation`: 387 × `lineage_less_room: missing source-row and frame lineage`. Source: `work/build4/rows_final_source/slices_v3/sealed_vqa_room_size_estimation/materialization.json`.
- `slices_final/a0_pool_abs_distance_reworded`: 19 × `needs frame metadata: supply the pinned frame_map join before intake`. Source: `work/build4/rows_final_source/slices_final/a0_pool_abs_distance_reworded/materialization.json`.

These causes are not waived: the shared grammar rejects unsupported quantities, exhaustive frame assertions and missing reasoning; direct-only rows cannot enter the event path; raw room rows lack required source/frame lineage; clock joins refuse missing or contradictory evidence. Older pool rows retain their original wording. Contract patches remain out of scope.

## CPU proofs and package

The native producer/reader proofs use synthetic RGB and TinyProcessor at the pretrained input interface. The separate model proof runs native forward/backward with tiny random weights and synthetic vision tensors. These are explicit stand-ins, not a proof with the real pretrained RGB processor, towers or export. Sources: `work/build4/tests_current/B3_NATIVE_JOB_PROOF.json`, `B3B_NATIVE_PROOF.json`, `B2_MODEL_PROOF.json` and the associated test files.

Temporary test products become permanent proof artifacts by rename after the per-test size check; each run records original-to-final paths in `artifact_locations.json`. Nothing is discarded or copied as a store/checkpoint. Earlier aborted attempts are retained and are not counted as passes.

- Package run (all tree modules): None tests run, unrecorded discovered, exit 1, 0 failures, 0 errors, unrecorded skips. Source: `work/build4/package_1794785829197894938/PACKAGE_RESULT.json`. The run stopped before completing its suite. A zero or null count is not a pass.
- Package run (all tree modules): None tests run, unrecorded discovered, exit 130, 0 failures, 43 errors, 4 skips. Source: `work/build4/package_1794786224789770885/PACKAGE_RESULT.json`. The run stopped before completing its suite. A zero or null count is not a pass.
- Package run (R2 modules only): 235 tests run, 235 discovered, exit 1, 0 failures, 1 errors, 0 skips. Source: `work/build4/package_1794786581946641940/PACKAGE_RESULT.json`. A zero or null count is not a pass.
- Package run (all tree modules): 0 tests run, 2177 discovered, exit 1, 0 failures, 0 errors, 0 skips. Source: `work/build4/package_1794787256256291931/PACKAGE_RESULT.json`. The run stopped before completing its suite. A zero or null count is not a pass.
- Final extracted-package delta check: 68 tests, 0 failures and 0 errors. Source: `work/build4/package_final_delta/results.json`. This checks the final grammar wrapper and the corrected environment-clearing harness path; it does not qualify the full suite.

The complete package requirement remains unmet. Legacy tests still require external inputs or subprocess behavior forbidden during this run. The final all-tree attempt reached the lane reserve before its first test. The package bundles the current kits as compressed archives under `work/build4/kits`; the standalone restaged kit directories are also delivered. The earlier R2 suite used the preceding grammar wrapper; final wrapper tests are recorded separately. A prior all-tree run was deliberately interrupted to close the child-process audit boundary; its receipt records the interruption, not a cluster kill.


Changed-statement coverage across the diff from the original base is 3046/3434. 388 unexecuted statements remain conservatively classified as CPU-reachable unresolved. This fails the requested zero-gap criterion. Source: `work/build4/CHANGED_COVERAGE.json`. Only hash-matched current-file executions count; historical line hits are not assumed valid.

Final artifact identity, required validator/exclusion pins, slice accounting and review-source identity are recorded in `work/build4/FINAL_AUDIT.json`. Resource use is recorded in `work/build4/FINAL_STORAGE.json`. The current tree still refuses readiness; storage limits and missing authorized inputs constrain further proof work.

## For the second review

- Recheck the current published-row envelope, masked raw pool path, converted-unit and simulated-miss behavior using `work/build4/rows_final_source/RESULTS.json` and the immutable envelopes in `rows_complete`.
- Rerun the row/bank harness and statement mutations from `work/build4/review_harness.py` and `review_mutcov.py`; both preserve original probe bodies/strings where applicable.
- Inspect staging-list completeness separately from actual parent archive/namespace restoration. The latter remains an admission blocker.
- Inspect upload callbacks separately from durable full-state restore. Uploader stand-ins establish ordering and verification, not remote recovery.
- Check final source/config seals and the unsigned authorization before any further work. Empty bank catalog, missing vocabulary and missing component evidence keep this leg closed.

Not checked: actual pinned venv/bwrap execution; full parent archive contents and nested native paths; full-store frame-host reconstruction and post-refusal sampler reindexing; actual pretrained vocabulary; real bank membership; real checkpoint restore/upload deadlines/resources; distributed GPU behavior, fit, performance or benchmark results. No source outside the named lane inputs was fetched.

## Artifacts

Tree: `work/tree_r1`. Inventory/diff/seal: `out/TREE_FILES.sha256`, `out/TREE.diff`, `out/TREE_SEAL.json`. Tree digest: `0fc11a63209cc6e73827149a78dea070aa72f279ec3ed7f79d8d3777be3f4320` (source: `out/TREE_SEAL.json`).

- `work/build4/kits/a0`: `1d07d046b61f379831a292095bcef7277188799fdf02932c41a2414da21443b8` (source: `work/build4/kits/RESULTS.json`).
- `work/build4/kits/a2`: `efd3e88d83da3d5422c73edb01916aeebd294ac45e978af151d015149b79907f` (source: `work/build4/kits/RESULTS.json`).
