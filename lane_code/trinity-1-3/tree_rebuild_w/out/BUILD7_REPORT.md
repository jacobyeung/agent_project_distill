# Build 7 — BLOCKED; neither kit is launchable

The tree and kits contain the input gates, policy additions and patch integrations below. This build does not qualify the requested product. Missing production inputs, incomplete code integration, unqualified reader paths and failed checks remain explicit blockers. Nothing was launched or submitted.

Source seal: `26a635fc34aa97ac2909985ca4c1e1007c03e621ab95742d2a7c93a7b282b052` (`out/TREE_SEAL.json`).

Package: `out/tree_rebuild_b7_26a635fc.tar`; SHA256 `3580d2f4034d4282f76280dd87526d3975d821eff89ae3e86ecfe4235d4ed0e0`; bytes 107018240 (`work/build7/DELIVERY.json`). The inventory and base-relative diff are `out/TREE_FILES.sha256` and `out/TREE.diff`.

## Requested items

“Blocked” distinguishes completed local work from the missing evidence or code still required. The item numbers follow the build request.

| Item | Status | Result and remaining blocker | Evidence |
|---|---|---|---|
| 1 | Closed locally; remote unverified | Staging mappings use the supplied source pins and archive member inventory. Frame-host self-check authenticates source bytes before staging. No Orchard source was read. | `work/tree_r1/launch_r2/staging_sources.json; work/tree_r1/launch_r2/input_check.py; tests.test_r2_build7.InputTests.test_sources_pass_absent_sha_and_member_refusal` |
| 2 | Blocked: init_selection_pending | Init stays a pinned rule-selected parameter; temporary sources and mismatched hashes refuse. No candidate was selected. Record dependencies are enumerated separately. | `work/tree_r1/student_pilot/b7_inputs.py; work/build7/proofs/review/INIT_DEPENDENCIES.json` |
| 3 | Blocked: rows_lane_store_bindings_missing | Family pins require D0 v5 and admitted A0/A2 sources and reject the sealed stores. The host binds each supplied family manifest to those pins before the existing native materializer combines streams. Missing or unbound manifests refuse. Production pins remain absent. | `work/tree_r1/student_pilot/b7_inputs.py; work/build7/proofs/input_binding/results.json` |
| 4 | Blocked: gf1_real_dense_manifest_missing | The synthetic clip is absent from kit staging. A2 requires the real GF-1 manifest under the dense plan; no local fixture substitutes for it. | `work/tree_r1/student_pilot/r2_config.py; work/build7/kits/RESULTS.json` |
| 5 | Closed | The empty exclusion-list files remain as authenticated zero-row lists. They preserve parent list provenance and exclude no row. | `work/tree_r1/student_pilot/row_removals.py:31; work/build7/proofs/review/KIT_READCHECK.json` |
| 6 | Blocked: processor_resolution_pin_missing; full parent inventory unqualified | Both kits carry explicit required resolution parameters and per-module trainability/rates. Tiny-model optimizer membership equals requires_grad. Real bound processor values and full parent-model validation are unavailable. | `work/build7/PROCESSOR_SEARCH.json; work/build7/proofs/review/KIT_READCHECK.json; work/build7/proofs/targeted_final/scale/RESULT.json` |
| 7 | Closed locally; stage limitation recorded | Positive scale weight is pinned in both kits. The real pose target producer supplies geometry-derived d-bar and the tiny scale loss backpropagates to the scale MLP. Existing connector-only A2 stage freezes that head; its subsequent joint stage can train it. Reader scale source is unchanged. | `work/build7/proofs/targeted_final/scale/RESULT.json; work/build7/proofs/review/KIT_READCHECK.json; work/build7/DECISIONS.md` |
| 8 | Blocked: ALL_FORMATTERS_NOT_QUALIFIED | Versioned module and JSON are pinned; bounded printed responses round-trip. Inline and multiline bound envelopes remain distinct. Complete producer/runtime formatter coverage and canonical field reconstruction remain unproved. | `work/tree_r1/student_pilot/response_spec.py; work/tree_r1/student_pilot/response_spec.json; work/build7/proofs/rows/RESULTS.json` |
| 9 | Blocked: ROWS_RULE_TEXT_PRESENT (rows lanes) | Row admission refuses detected rule-only text. Bounded slices contain unavailable/not-seen statuses. Numeric tower-rule provenance cannot be inferred from text alone. Rows were not edited. | `work/tree_r1/student_pilot/row_text_audit.py; work/build7/proofs/review/RESPONSE_RULE_SOURCES.json; work/build7/proofs/rows/RESULTS.json` |
| 10 | Closed label gate; no passing production receipt | Kits default to harness_served and claim neither room form. The gate consumes the actual EAT report schema and requires passing dynamic clauses plus the reader artifact digest. Fixture pass, failure and wrong-artifact refusals pass. No model_served claim is made. | `work/tree_r1/student_pilot/b7_inputs.py:53; work/build7/proofs/input_binding/results.json` |
| 11 | Blocked: FRAME64_ALL_READERS_UNQUALIFIED; OUTSIDE_FORWARD_FORMATTING | Core encoder, carrier/readout capacity, pose targets and export support pinned frame counts. All ground/MDG/read paths are not qualified. Final answer passthrough is tested; tool-value formatting remains outside forward. ReVSI is listed first; kits default to SFT. | `work/build7/proofs/targeted_final/frames/TOKENS.json; work/build7/proofs/audit/NUMBER_PATHS.json; work/build7/proofs/review/KIT_READCHECK.json` |
| 12 | Blocked: ROWS_MINORITY_FORMS_UNBOUND; LEGACY_DIRECT_SOURCE_TRACE_UNQUALIFIED; INDEPENDENT_REVIEW_PENDING | Both policy, separate type gate, per-item answer_form and pinned minority sampler are implemented. Missing head grammars refuse program rows; room stays direct. Native end-to-end store sampling and all legacy-policy byte parity remain unproved. The separate legacy direct-source builder still constructs empty-think traces and is not qualified for this policy. Recovery form is deferred. | `work/tree_r1/student_pilot/routing_type_gate.py; work/tree_r1/student_pilot/carrier_c1_routing.py:888; work/build7/DECISIONS.md; work/build7/proofs/rows/RESULTS.json` |
| 13 | Blocked: R0_FULL_INPUT_INVENTORY_UNAVAILABLE | Pinned R0 authority and alias-family refusals are implemented. Available slices were scanned. Full staged frames, caches and every stream are unavailable; unknown overlap is not admitted. | `work/tree_r1/student_pilot/r0_exclusion.py; work/build7/proofs/audit/AUTHORITY_HASHES.json; work/build7/proofs/rows/RESULTS.json` |
| 14 | Blocked: BF16_CACHE_GRADIENT_PARITY; INDEPENDENT_REVIEW_PENDING | Cache patch rebased; option is off with FP32 default. Enabled BF16 is refused by kits. Supplied BF16 gradient tolerance still fails and was not widened. Cache tests and OFF behavior remain in the suite. | `work/build7/PATCH_HUNKS.json; work/build7/proofs/targeted/results.json; work/tree_r1/tests/test_gf1_cache.py` |
| 15 | Blocked: B04_FORWARD_HOOK_REQUIRED; PORTRAIT_MASK_DISTORTION | Native tiny export/reload emits an artifact manifest and declared module roles. Full read-file closure is not qualified. Stencil, degree and status computations remain outside forward; portrait mask paths remain distorted to preserve bound-row bytes. EAT results follow below. | `work/tree_r1/student_pilot/eat1_export.py; work/build7/proofs/eat1; work/build7/proofs/audit/RESIZE_AUDIT.json` |
| 16 | Blocked: BOUND_FAITHFUL_IDENTITY_RECEIPT_MISSING; FULL_ENCODER_PARITY_UNQUALIFIED | Faithful patch rebased behind an off-by-default switch. Materializer exists; fixture identity gate refuses insufficient identity. Native tiny losses, gradients, batches, legacy policy data and own-value suffix masks match the authenticated build-6 source. Full scheduled-sampling encoder parity and bound routing identity remain unqualified. | `work/build7/PATCH_HUNKS.json; work/build7/proofs/off_parity/RESULTS.json; work/build7/proofs/targeted_final/results.json` |
| 16a | Blocked: GLOO_INITIALIZATION; MULTIRANK_END_SLOT_UNPROVED | Shell stop-file paths and rank polling are connected. Real trap/poll proof passed. Gloo could not initialize; the full wrapper chain and multi-rank end slot remain unproved. The single-rank native fallback stops, exports and reloads its end slot. | `work/build7/proofs/stop/RESULTS.json; work/build7/proofs/review/STOP_PATH.json; work/build7/proofs/final_targeted/stop_fallback/RESULT.json` |
| 17 | Blocked: SUITE_OR_COVERAGE_CRITERIA_UNMET | Final frozen package groups and packet suite are recorded below. Failures and CPU gaps remain failures, including new ones. | `work/build7/FINAL_PASS.json; work/build7/SUITE_COMPARISON.json; work/build7/CHANGED_COVERAGE.json` |
| 18 | Closed staging; GO=false | Both final kits were staged from empty, A2 first, scanned and authenticated. Their source pins match the frozen tree. | `work/build7/proofs/review/KIT_READCHECK.json; work/build7/proofs/package/KIT_TESTS.json` |
| 19 | Closed comparison | Build-6 regressions and gaps are individually mapped below. Build 6 was not separately finalized. Package groups have input-hash-bound resume receipts. | `work/build7/BUILD6_DISPOSITION.json; work/build7/package.py` |

## Suites and coverage

Packet: {"run": 202, "passed": 202} (`work/build7/proofs/packet/results.json`). The harness executes the original tests under `work/contracts_r6/packet_root/work/tests_r6`, relocating input/output paths in memory. Their assertions remain unchanged.

| Package variant | Run | Passed | Failure events | Error events | Skipped | Complete | Source |
|---|---:|---:|---:|---:|---:|---|---|
| tree | 2216 | 1672 | 17 | 461 | 145 | True | `work/build7/proofs/suite_tree/results.json` |
| base | 1842 | 1302 | 14 | 460 | 145 | True | `work/build7/proofs/suite_base/results.json` |

Initial supplemental run: {"run": 24, "passed": 23, "failures": 0, "errors": 1, "complete": true} (`work/build7/proofs/final_targeted/results.json`).

- Initial supplemental error `coverage_b7.FaithfulRows.test_native_readout_runs_even_when_local_row_is_refused`: ValueError: Routing streams require training_mode final (`work/build7/proofs/final_targeted/results.json`). Latest follow-up outcome: passed (`work/build7/FOLLOWUP_RESULTS.json`).

Supplemental follow-ups retain every attempt: {"executions": 40, "latest_case_outcomes": {"passed": 34}} (`work/build7/FOLLOWUP_RESULTS.json`). Fixture corrections use final-mode camera readout, preserve the private-ViT merger exception, invoke the cache as a package module, and keep pinned source bytes outside the temporary folder. They do not change the frozen tree or its package-suite failures.

The native cache CLI wrote and reread a finite synthetic bank, and its repeat write preserved the tensor bytes. The native kit builder also exercised required and fixture-selected inputs. Evidence: `work/build7/proofs/coverage_final/cache/PROOF.json`, `work/build7/proofs/coverage_final/cache_read/RESULT.json`, and the attempt receipts in `work/build7/FOLLOWUP_RESULTS.json`. The cache proof substitutes a seeded tiny registered tower, its input raster and its unavailable production weight load; it does not qualify production weights.

Comparison: {"run": 2216, "passed": 1672, "preexisting": 474, "regressions": 4, "r2_failures": 2, "skipped": 145} (`work/build7/SUITE_COMPARISON.json`). All failure names, causes and paired base traces are retained there. Execution counts include repeated test IDs; subtest and setup errors can add failure events.

Current regressions (`work/build7/SUITE_COMPARISON.json`):

- `tests.test_gf1_cache.CachedBank.test_parity_cached_vs_online`: BF16 cached/online gradient exceeds the supplied relative tolerance; enabled BF16 remains refused.

- `tests.test_r2_build5_edges.Edges.test_plan_unknown_inputs_and_worker_environment`: R2 fixture expects placeholder staging parts; unknown sources now require an explicit pinned parameter.

- `tests.test_r2_build5_host_order.HostOrder.test_full_host_stages_before_packet_byte_validation`: R2 host-order fixture omits the runtime file pin required by the new staging self-check.

- `tests.test_carrier_c1_run.RunnerTests.test_train_enables_native_decoder_checkpointing_after_eval_load`: Legacy training fixture lacks the tokenizer required by the new frame-count binding at carrier_c1_run.py:1206.

Previously failing base test IDs now passing: 0 (`work/build7/FIXED_BASE_FAILURES.json`); these exact-ID fixes are distinct from new tests and from repeated execution counts.

| Changed-statement class | Count | Source |
|---|---:|---|
| observed | 5716 | `work/build7/CHANGED_COVERAGE.json` |
| frame-host | 78 | `work/build7/CHANGED_COVERAGE.json` |
| CPU-reachable unresolved | 78 | `work/build7/CHANGED_COVERAGE.json` |
| GPU | 3 | `work/build7/CHANGED_COVERAGE.json` |
| model-loader | 2 | `work/build7/CHANGED_COVERAGE.json` |

Coverage uses standard-library sys.monitoring, AST changed-statement heads, compiled-code fingerprints and exact current-file hashes. No inference from adjacent lines counts as coverage. Builds through this final tree are compared with the untouched base; integrated packet lines enter the same denominator. `work/build7/GAPS.json` lists unresolved CPU lines. External classifications state missing inputs.

Build-6 regression disposition (`work/build7/BUILD6_DISPOSITION.json`):

- `generator.derivgen_v7.test_v312_quality.QualityTests.test_qualifier_must_equal_literal_gt_label`: resolved; passed on final source.

- `tests.test_c1_validation_slice.ValidationPreparation.test_validation_config_is_optional_and_requires_exact_pins`: resolved; passed on final source.

- `tests.test_gxp_mix.MemoryFallback.test_absent_keys_preserve_normalized_identity_and_fp32_output_bytes`: resolved; passed on final source.

- `tests.test_s1_launch_kit.LaunchKitTests.test_all_eight_ranks_and_native_configuration_binding_are_required`: resolved; passed on final source.

Build-6 gap mapping: {"resolved": 221} (`work/build7/BUILD6_DISPOSITION.json`); the original per-file gaps remain in `work/build6/GAPS.json`. Ambiguous textual mappings remain open.

## Kit pins and model behavior

A2: SHA256 `87d521014bd3f6c8e1386df92189527be393f415d892bd46baaba6195c7eafb5`; scanner CLEAN (`work/build7/proofs/review/KIT_READCHECK.json`). Layout: `{"max_pixels": null, "min_pixels": null, "frame_count": 32, "frame_layout": "duplicate", "frame_markers": true}`. Trainable list: `{"base_vit": {"learning_rate": 0.0, "trainable": false}, "depth_head": {"learning_rate": 0.0001, "trainable": true}, "lm": {"learning_rate": 6e-06, "trainable": true}, "merger": {"learning_rate": 0.0, "trainable": false}, "pose_head": {"inherited_learning_rate": 1e-05, "learning_rate": 6e-05, "trainable": true}, "private_vit": {"learning_rate": 0.0, "source": "load_depth_stage1", "trainable": false}}`.

A0: SHA256 `8259dbab7e6c595d7d5475b578e41390b6259d744bf83b38bcd55fb0cadd6d77`; scanner CLEAN (`work/build7/proofs/review/KIT_READCHECK.json`). Layout: `{"max_pixels": null, "min_pixels": null, "frame_count": 32, "frame_layout": "duplicate", "frame_markers": true}`. Trainable list: `{"base_vit": {"learning_rate": 0.0, "trainable": false}, "depth_head": {"learning_rate": 0.0001, "trainable": true}, "lm": {"learning_rate": 6e-06, "trainable": true}, "merger": {"learning_rate": 0.0, "trainable": false}, "pose_head": {"inherited_learning_rate": 1e-05, "learning_rate": 6e-05, "trainable": true}, "private_vit": {"learning_rate": 0.0, "source": "load_depth_stage1", "trainable": false}}`.

The module list follows the existing full_ft/final-mode optimizer; loading the bound private-depth initialization freezes its private ViT. The connector-only stage separately freezes the other modules. `artifact.json` records actual named-parameter membership on export. The tiny-model list is not proof that an absent full checkpoint has the same inventory.

The scale weight is **GUESS 1.0**, equal to the final-mode gravity weight (`work/build7/build_kits.py`). The real `pose_samples.encode_sample` and `camera_targets.trajectory_scale` produce per-clip d-bar; the existing head loss takes its logarithm. Measured loss and gradient parameter names are in `work/build7/proofs/targeted_final/scale/RESULT.json`. No benchmark answer chooses the target or weight.

The native `CarrierC1.readout` exposes `trajectory_step_m`; `HeadState` currently discards the scale output and its downstream geometry still uses the existing scale source. `student_pilot/tower_scale.py` and `tower_scale_rule.py` remain unchanged in their scale-source behavior. Consuming the head scale needs the in-forward reader hook; this build does not switch it.

Tiny-model frame measurements: `[{"frame_count": 32, "visual_tokens": 32, "carriers": 32}, {"frame_count": 64, "visual_tokens": 64, "carriers": 64}]` (`work/build7/proofs/targeted_final/frames/TOKENS.json`). This uses the tiny native model with one visual token per frame, not D0 resolution. **GUESS:** doubling frame count doubles visual tokens and approximately doubles visual/activation storage; attention work can approach fourfold. Actual GPU memory/time is unmeasured. D0-resolution token counts await its processor pin.

The routed query tensor still fixes its frame dimension in `student_pilot/carrier_c1_routing.query_tensor`. Additional ground, MDG and camera-row assumptions are enumerated with file:line in `work/build7/proofs/audit/FRAME64_REMAINING_SITES.json`. These are local implementation or compatibility-proof gaps, not missing production pins. The kit’s FRAME64_ALL_READERS_UNQUALIFIED blocker remains in force.

The empty exclusion lists remain pinned to the empty-file digest. `Removals.__init__` reads only nonblank lines (`work/tree_r1/student_pilot/row_removals.py:31`) and `keep` tests membership in the resulting empty sets. They are zero-effect provenance entries, not missing data inferred to be clean.

Init dependencies for every record are in `work/build7/proofs/review/INIT_DEPENDENCIES.json`. The selected export, pose head, depth head and frame embeddings depend directly on the selection. Private-depth and connector records depend on whether the selected export supplies those components; other component records retain their independent provenance obligations.

Native synthetic camera rows pass materializer identity: {"rows": 2, "identical": 2, "different": 0, "refused": 0, "identity_rate": 1.0} (`work/build7/proofs/final_targeted/faithful/IDENTITY.json`). The focused test also checks re-derived text after changing the synthetic pose geometry. This fixture rate does not replace the required identity measurement on the bound routing store.

The native suffix-mask unit proof retains 83 tokens after the own response with faithful supervision enabled, versus 0 with it disabled (`work/build7/proofs/final_targeted/faithful/MASKS.json`). It uses a synthetic processor/tokenizer fixture and does not qualify the unavailable bound tokenizer or the full training encoder.

## Bound slices, response text and exclusions

| Slice | Rows read | Rule-only status rows | Responses / exact round-trips | R0 matches | Portrait frames | Source |
|---|---:|---:|---|---|---|---|
| a0_pool_abs_distance_reworded.jsonl | 2000 | 0 | 6000 / 6000 | 0 | Unknown; dimensions absent | `work/rows_slices/slices_final/a0_pool_abs_distance_reworded.jsonl` |
| a0_recovery.jsonl | 1532 | 1532 | 2295 / 2295 | 0 | Unknown; dimensions absent | `work/rows_slices/slices_final/a0_recovery.jsonl` |
| a0_room.jsonl | 476 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `work/rows_slices/slices_final/a0_room.jsonl` |
| a0_units.jsonl | 2000 | 0 | 6000 / 6000 | 0 | Unknown; dimensions absent | `work/rows_slices/slices_final/a0_units.jsonl` |
| a0_recovery.jsonl | 3 | 3 | 4 / 4 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/a0_recovery.jsonl` |
| a0_room.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/a0_room.jsonl` |
| a0_units.jsonl | 0 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/a0_units.jsonl` |
| d0_facing_easy.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_facing_easy.jsonl` |
| d0_facing_hard.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_facing_hard.jsonl` |
| d0_facing_medium.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_facing_medium.jsonl` |
| d0_retrace_box_3d.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_retrace_box_3d.jsonl` |
| d0_retrace_obj_appearance_order.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_retrace_obj_appearance_order.jsonl` |
| d0_retrace_object_counting.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_retrace_object_counting.jsonl` |
| d0_retrace_object_rel_direction_easy.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_retrace_object_rel_direction_easy.jsonl` |
| d0_retrace_object_rel_direction_hard.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_retrace_object_rel_direction_hard.jsonl` |
| d0_retrace_object_rel_direction_medium.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_retrace_object_rel_direction_medium.jsonl` |
| d0_retrace_object_rel_distance.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_retrace_object_rel_distance.jsonl` |
| d0_retrace_object_size_estimation.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_retrace_object_size_estimation.jsonl` |
| d0_route_planning.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_route_planning.jsonl` |
| d0_totals.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/d0_totals.jsonl` |
| pool_abs_distance.jsonl | 0 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/pool_abs_distance.jsonl` |
| pool_room.jsonl | 3 | 0 | 3 / 3 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/pool_room.jsonl` |
| pool_route_planning.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/pool_route_planning.jsonl` |
| sealed_vqa_box_3d.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_box_3d.jsonl` |
| sealed_vqa_obj_appearance_order.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_obj_appearance_order.jsonl` |
| sealed_vqa_object_abs_distance.jsonl | 0 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_object_abs_distance.jsonl` |
| sealed_vqa_object_counting.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_object_counting.jsonl` |
| sealed_vqa_object_rel_direction_easy.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_object_rel_direction_easy.jsonl` |
| sealed_vqa_object_rel_direction_hard.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_object_rel_direction_hard.jsonl` |
| sealed_vqa_object_rel_direction_medium.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_object_rel_direction_medium.jsonl` |
| sealed_vqa_object_rel_distance.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_object_rel_distance.jsonl` |
| sealed_vqa_object_size_estimation.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_object_size_estimation.jsonl` |
| sealed_vqa_room_size_estimation.jsonl | 3 | 0 | 0 / 0 | 0 | Unknown; dimensions absent | `fixtures/rows/slices_v3/sealed_vqa_room_size_estimation.jsonl` |

All slice counts and consumed-slice hashes come from `work/build7/proofs/rows/RESULTS.json`. Each digest covers only the rows read from that file, in order; it does not authenticate an unread remainder. Overlapping fixture and real slices are not a population estimate.

R0 matches are inspected-row matches only. No row files were modified, so no physical removal is claimed. Full pose, pointing, raster, depth, dense-frame and cache inventories were not supplied; their removed counts and overlap are unknown. The kits refuse unknown full-input qualification.

The format module preserves the bound inline camera/calculator envelope and newline ground envelope; signed deltas, metric decimals, integer degree angles and status literals retain their printed bytes. These existing variants are represented explicitly rather than normalized. The parser preserves the body instead of reconstructing every semantic field, so full canonical formatting is still open. Patterns and actual print sites are in `work/build7/proofs/review/RESPONSE_RULE_SOURCES.json`. Heuristic text matches cannot certify that a numeric value came from a head.

## EAT-1 and outside-weight inference components

| Clause | Supplied build-5 GF-1 baseline | Build-7 GF-1 tiny | Build-7 C8r tiny |
|---|---|---|---|
| A1 | PASS (tower weights declared) | PASS | PASS |
| A2 | FAIL | FAIL | FAIL |
| A3 | FAIL | FAIL | FAIL |
| A4 | FAIL | FAIL | FAIL |
| A5 | PASS | INCOMPLETE | INCOMPLETE |

Sources: `work/design/eat1_b03/out/BASELINE_A2_TREE.md`; `work/build7/proofs/eat1/gf1/run/EAT1_REPORT.json`; `work/build7/proofs/eat1/c8r/run/EAT1_REPORT.json`. Static scope was copied and rewritten to this tree in `work/build7/proofs/eat1/SCOPE_READ.txt`.

A5 is incomplete because the supplied runner reports its cache-proof clause as NOT RUN; tower execution and perturbation clauses pass. The baseline’s aggregate PASS must not substitute for the missing clause (`work/build7/proofs/eat1/gf1/run/EAT1_REPORT.json`).

Build-7 static findings by class: `{"A3.constant": 288, "A3.table_load": 32, "A3.data_file": 20, "A5.cache": 12, "A4.status_literal": 58, "A3.threshold": 76, "A4.guard": 49, "A2.response_outside_model": 16, "A4.except_substitute": 9, "A3.unit_conversion": 13}` (`work/build7/proofs/eat1/SCAN_READ.json`). Baseline class counts are recorded in `work/design/eat1_b03/out/BASELINE_A2_TREE.md`.

| Static finding class | Supplied build-5 baseline | Build-7 scope |
|---|---:|---:|
| cache | 12 | 12 |
| constant | 290 | 288 |
| data_file | 20 | 20 |
| except_substitute | 9 | 9 |
| guard | 48 | 49 |
| response_outside_model | 17 | 16 |
| status | 52 | 0 |
| status_literal | 0 | 58 |
| table_load | 32 | 32 |
| threshold | 76 | 76 |
| unit_conversion | 15 | 13 |

Table sources: `work/design/eat1_b03/out/BASELINE_A2_TREE.md`, section 1, and `work/build7/proofs/eat1/SCAN_READ.json`. Counts are scanner findings, not independent defects or acceptance passes.

The supplied tiny adapters use tiny pretrained-module stand-ins, a scripted token policy for exercising calls, seeded connector perturbations and no live ground session. Their findings qualify those fixture paths only. They are acceptance-test scaffolding, not a new product selector. Native tiny export/reload uses only one-rank collective/state-collection stand-ins; the real export and reader functions run.

Remaining outside-forward computations include the depth stencil in `student_pilot/geometry_profiles.py`, degree conversions in `student_pilot/carrier_c1_routing.py` and `trace_format/box_v313.py`, statuses in the box module, response injection in `carrier_c1_batch_decode.py`, typed errors in `carrier_c1_decode.py`, and calibrated MDG tau. Their exact current lines appear below and in `RESPONSE_RULE_SOURCES.json`. They remain assigned to the in-forward hook or named build blockers; moving a function name alone would not satisfy forward execution.

No final-answer unit conversion was found in the inspected `evalpath.runtime.generate` path; it returns decoded model text unchanged, as the passthrough fixture verifies. Tool-response number formatting is still outside the weights and is not claimed compliant. `work/build7/proofs/audit/NUMBER_PATHS.json` lists each discovered formatting/conversion site. The scan is conservative, not a proof of every dynamic product path.

| Formatting/conversion location | Existing operation |
|---|---|
| `work/tree_r1/trace_format/box_v313.py:98` | `yaw = int(number(np.degrees(np.arctan2(-direction[2],direction[0])),0))` |
| `work/tree_r1/trace_format/box_v313.py:112` | `yaw = int(number(np.degrees(np.arctan2(-d[2], d[0])), 0))` |
| `work/tree_r1/trace_format/box_v313.py:114` | `t = np.radians(yaw); d = np.array([np.cos(t), 0., -np.sin(t)]); e = np.cross(up, d)` |
| `work/tree_r1/trace_format/box_v313.py:122` | `theta=np.radians(yaw);c,s=np.cos(theta),np.sin(theta)` |
| `work/tree_r1/trace_format/box_v313.py:152` | `theta=np.radians(v[6]);c,s=np.cos(theta),np.sin(theta)` |
| `work/tree_r1/trace_format/box_v313.py:255` | `return '\n'.join(lines+[f'min {winners} {minimum:.2f} m']),values` |
| `work/tree_r1/trace_format/box_v313.py:279` | `return '\n'.join([f'{n}: {d} m' for n,d in zip(names,printed)]+[f'min {winners} {minimum:.2f} m']),values` |
| `work/tree_r1/trace_format/room_v314.py:188` | `r = int(round(CLOSING_M / CELL_M))` |
| `work/tree_r1/trace_format/room_v314.py:197` | `if float(f'{area:.2f}') <= 0:` |
| `work/tree_r1/trace_format/room_v314.py:205` | `height = f"{result['floor_height_m']:.2f}"` |
| `work/tree_r1/trace_format/room_v314.py:212` | `f"area {result['area_m2']:.2f} m^2")` |
| `work/tree_r1/trace_format/room_v314.py:226` | `expected = f'{int(m[3]) * CELL_M * CELL_M:.2f}'` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:108` | `return round(float(x), 2) + 0.0` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:112` | `return f'{r2(x):.2f}'` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:116` | `return f'{r2(x):+.2f}'` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:128` | `return np.round(np.asarray(a, dtype=np.float64), 8) + 0.0` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:309` | `yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:371` | `turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))` |
| `work/tree_r1/student_pilot/ground_lifting.py:20` | `text = f'{float(value):.2f}'` |
| `work/tree_r1/student_pilot/ground_lifting.py:237` | `lines.append('min ' + ','.join('"' + name + '"' for name in names) + f' {minimum:.2f} m')` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:120` | `return name + ': ' + (' &#124; '.join(f'f{i+1} [{int(uv[i][0])},{int(uv[i][1])}] {prob[i]:.2f}'` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:136` | `or not torch.equal(uv, uv.round())):` |

Conservative inference component inventory, with file:line for review (`work/build7/proofs/audit/INFERENCE_COMPONENTS.json`). Module-level functions are outside registered weights; backend methods need dynamic forward-scope judgment. This includes support/scoring functions and does not assert that every entry executes for every item. It does not replace the acceptance test.

| Location | Component |
|---|---|
| `work/tree_r1/evalpath/run.py:15` | `key` |
| `work/tree_r1/evalpath/run.py:19` | `shard_items` |
| `work/tree_r1/evalpath/run.py:25` | `read_journal` |
| `work/tree_r1/evalpath/run.py:42` | `pending_items` |
| `work/tree_r1/evalpath/run.py:46` | `append_record` |
| `work/tree_r1/evalpath/run.py:55` | `write_json` |
| `work/tree_r1/evalpath/run.py:61` | `worker_error` |
| `work/tree_r1/evalpath/run.py:70` | `score_item` |
| `work/tree_r1/evalpath/run.py:92` | `aggregate` |
| `work/tree_r1/evalpath/run.py:142` | `load_request_items` |
| `work/tree_r1/evalpath/run.py:156` | `binding_for` |
| `work/tree_r1/evalpath/run.py:164` | `validate_request` |
| `work/tree_r1/evalpath/run.py:207` | `run_worker` |
| `work/tree_r1/evalpath/run.py:217` | `_run_worker` |
| `work/tree_r1/evalpath/run.py:387` | `merge` |
| `work/tree_r1/evalpath/run.py:425` | `main` |
| `work/tree_r1/evalpath/runtime.py:5` | `verify_trainer` |
| `work/tree_r1/evalpath/runtime.py:25` | `evaluator_init_spec` |
| `work/tree_r1/evalpath/runtime.py:30` | `check_init_spec` |
| `work/tree_r1/evalpath/runtime.py:56` | `load_model` |
| `work/tree_r1/evalpath/runtime.py:119` | `teacher_batch` |
| `work/tree_r1/evalpath/runtime.py:131` | `prompt_batch` |
| `work/tree_r1/evalpath/runtime.py:151` | `generate` |
| `work/tree_r1/ofs/core.py:29` | `Proposal.joint` |
| `work/tree_r1/ofs/core.py:42` | `Candidate.voxels` |
| `work/tree_r1/ofs/core.py:46` | `Candidate.center` |
| `work/tree_r1/ofs/core.py:50` | `small_rle` |
| `work/tree_r1/ofs/core.py:65` | `voxel_set` |
| `work/tree_r1/ofs/core.py:69` | `lift_grid` |
| `work/tree_r1/ofs/core.py:87` | `lift` |
| `work/tree_r1/ofs/core.py:125` | `UnionFind.__init__` |
| `work/tree_r1/ofs/core.py:128` | `UnionFind.root` |
| `work/tree_r1/ofs/core.py:134` | `UnionFind.join` |
| `work/tree_r1/ofs/core.py:139` | `UnionFind.groups` |
| `work/tree_r1/ofs/core.py:146` | `overlap` |
| `work/tree_r1/ofs/core.py:150` | `linked` |
| `work/tree_r1/ofs/core.py:157` | `link` |
| `work/tree_r1/ofs/core.py:196` | `visible_voxels` |
| `work/tree_r1/ofs/core.py:220` | `features` |
| `work/tree_r1/ofs/core.py:236` | `scene_candidates` |
| `work/tree_r1/ofs/core.py:261` | `select` |
| `work/tree_r1/ofs/core.py:315` | `empty_values` |
| `work/tree_r1/ofs/core.py:322` | `values_for` |
| `work/tree_r1/ofs/core.py:341` | `ground_from_values` |
| `work/tree_r1/ofs/core.py:351` | `candidate_json` |
| `work/tree_r1/ofs/core.py:359` | `export` |
| `work/tree_r1/ofs/hrp_reference.py:20` | `select` |
| `work/tree_r1/ofs/hrp_reference.py:86` | `centroid` |
| `work/tree_r1/ofs/hrp_reference.py:95` | `from_points` |
| `work/tree_r1/ofs/hrp_reference.py:111` | `select_keypoints` |
| `work/tree_r1/ofs/hrp_reference.py:143` | `_keypoint_distance` |
| `work/tree_r1/ofs/hrp_reference.py:166` | `keypoint_gap` |
| `work/tree_r1/ofs/hrp_reference.py:175` | `keypoint_extent` |
| `work/tree_r1/student_pilot/camera_targets.py:27` | `quaternion_xyzw` |
| `work/tree_r1/student_pilot/camera_targets.py:47` | `rotation_from_xyzw` |
| `work/tree_r1/student_pilot/camera_targets.py:54` | `rigid` |
| `work/tree_r1/student_pilot/camera_targets.py:61` | `trajectory_scale` |
| `work/tree_r1/student_pilot/camera_targets.py:68` | `encode_cameras` |
| `work/tree_r1/student_pilot/camera_targets.py:112` | `encode_gravity` |
| `work/tree_r1/student_pilot/camera_targets.py:126` | `gravity_reference_rotation` |
| `work/tree_r1/student_pilot/camera_targets.py:149` | `to_gravity_reference_frame` |
| `work/tree_r1/student_pilot/camera_targets.py:184` | `probe_record` |
| `work/tree_r1/student_pilot/camera_targets.py:213` | `check_record` |
| `work/tree_r1/student_pilot/camera_targets.py:238` | `load_for_rows` |
| `work/tree_r1/student_pilot/camera_targets.py:294` | `carrier_id` |
| `work/tree_r1/student_pilot/camera_targets.py:301` | `insert_tokens` |
| `work/tree_r1/student_pilot/camera_targets.py:345` | `insert_carriers` |
| `work/tree_r1/student_pilot/candidate_policy.py:13` | `predict` |
| `work/tree_r1/student_pilot/candidate_policy.py:25` | `depth_cut` |
| `work/tree_r1/student_pilot/candidate_policy.py:41` | `disjoint` |
| `work/tree_r1/student_pilot/candidate_policy.py:51` | `merge` |
| `work/tree_r1/student_pilot/candidate_policy.py:75` | `Policy.__post_init__` |
| `work/tree_r1/student_pilot/candidate_policy.py:85` | `Policy.select` |
| `work/tree_r1/student_pilot/carrier_c1_batch_decode.py:18` | `merge_caches` |
| `work/tree_r1/student_pilot/carrier_c1_batch_decode.py:56` | `select_cache_rows` |
| `work/tree_r1/student_pilot/carrier_c1_batch_decode.py:67` | `_row_values` |
| `work/tree_r1/student_pilot/carrier_c1_batch_decode.py:75` | `_tower_failure` |
| `work/tree_r1/student_pilot/carrier_c1_batch_decode.py:82` | `Row.__init__` |
| `work/tree_r1/student_pilot/carrier_c1_batch_decode.py:96` | `Row.step` |
| `work/tree_r1/student_pilot/carrier_c1_batch_decode.py:118` | `Row._call` |
| `work/tree_r1/student_pilot/carrier_c1_batch_decode.py:147` | `Row.record` |
| `work/tree_r1/student_pilot/carrier_c1_batch_decode.py:162` | `generate_batch` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:44` | `CallError.__init__` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:49` | `consume_cache_tokens` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:73` | `parse_head` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:97` | `parse_ground` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:106` | `parse_gap` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:118` | `ground_text` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:125` | `ground_predictions` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:143` | `HeadState.__init__` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:180` | `HeadState.ground` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:202` | `HeadState.depth` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:211` | `HeadState.geometry` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:215` | `respond` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:256` | `_prepare_decode` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:437` | `generate` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:461` | `_generate_one` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:481` | `ground_records` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:503` | `ground_layout_for` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:507` | `respond_state` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:516` | `_respond_state` |
| `work/tree_r1/student_pilot/carrier_c1_decode.py:543` | `replay` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:91` | `validate_tool_mode_flag` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:96` | `tool_mode` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:107` | `r2` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:111` | `f2` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:115` | `s2` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:119` | `vec` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:123` | `wrap` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:127` | `r8` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:132` | `render_full` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:180` | `render` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:185` | `check_row` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:206` | `level_basis` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:230` | `OwnGeometry.__init__` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:250` | `OwnGeometry.to_l1` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:257` | `OwnGeometry._basis` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:279` | `OwnGeometry.camera` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:291` | `OwnGeometry.fov` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:297` | `OwnGeometry.camera_pose` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:301` | `OwnGeometry.pose` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:312` | `OwnGeometry.click` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:333` | `OwnGeometry.pose_text` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:345` | `OwnGeometry.move_text` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:365` | `OwnGeometry.turn_text` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:377` | `RecordedGeometry.__init__` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:382` | `RecordedGeometry.click_label` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:386` | `RecordedGeometry.response` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:398` | `depth_queries` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:412` | `calculator_for` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:416` | `rerender` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:464` | `suffix_mask` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:498` | `suffix_tokens` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:505` | `segment_ids` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:516` | `finish` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:541` | `encode` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:551` | `encode_own` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:558` | `splice` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:576` | `prefix_batch` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:591` | `validate_schedule` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:619` | `Gates.__init__` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:623` | `Gates.update` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:631` | `Gates.state` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:649` | `Gates.decide` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:657` | `row_geometry` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:690` | `query_tensor` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:708` | `own_geometry` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:726` | `add_routing_tokens` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:742` | `init_routing_embeddings` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:756` | `c1_row` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:811` | `alias_of` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:818` | `camera_filter` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:847` | `load_exclusions` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:861` | `alias_key` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:869` | `alias_names` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:875` | `excluded` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:880` | `canonical_keys` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:887` | `direct_row` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:909` | `build_routing_stream` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:1044` | `main` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:1075` | `gt_replay` |
| `work/tree_r1/student_pilot/carrier_c1_routing.py:1100` | `shippable_exclusions` |
| `work/tree_r1/student_pilot/geometry_profiles.py:22` | `validate_up_convention` |
| `work/tree_r1/student_pilot/geometry_profiles.py:46` | `profile` |
| `work/tree_r1/student_pilot/geometry_profiles.py:75` | `GeometryContract.validate` |
| `work/tree_r1/student_pilot/geometry_profiles.py:121` | `GeometryContract.identity` |
| `work/tree_r1/student_pilot/geometry_profiles.py:138` | `ProfileGeometry.__init__` |
| `work/tree_r1/student_pilot/geometry_profiles.py:162` | `ProfileGeometry.has` |
| `work/tree_r1/student_pilot/geometry_profiles.py:165` | `ProfileGeometry.cam` |
| `work/tree_r1/student_pilot/geometry_profiles.py:170` | `ProfileGeometry.rays` |
| `work/tree_r1/student_pilot/geometry_profiles.py:174` | `ProfileGeometry._raw_depth` |
| `work/tree_r1/student_pilot/geometry_profiles.py:182` | `ProfileGeometry.depth` |
| `work/tree_r1/student_pilot/geometry_profiles.py:188` | `ProfileGeometry.to_world` |
| `work/tree_r1/student_pilot/geometry_profiles.py:194` | `ProfileGeometry.lift` |
| `work/tree_r1/student_pilot/geometry_profiles.py:205` | `ProfileGeometry.fov_of` |
| `work/tree_r1/student_pilot/geometry_profiles.py:213` | `ProfileGeometry._depth` |
| `work/tree_r1/student_pilot/geometry_profiles.py:219` | `ContractAdapter.__init__` |
| `work/tree_r1/student_pilot/geometry_profiles.py:240` | `ContractAdapter.__getattr__` |
| `work/tree_r1/student_pilot/geometry_profiles.py:244` | `legacy_from_heads` |
| `work/tree_r1/student_pilot/geometry_profiles.py:271` | `scaled_from_heads` |
| `work/tree_r1/student_pilot/ground_context.py:22` | `GroundContext.frame` |
| `work/tree_r1/student_pilot/ground_context.py:40` | `from_row` |
| `work/tree_r1/student_pilot/ground_context.py:56` | `closed_adapters` |
| `work/tree_r1/student_pilot/ground_lifting.py:19` | `number` |
| `work/tree_r1/student_pilot/ground_lifting.py:26` | `mask_pixels` |
| `work/tree_r1/student_pilot/ground_lifting.py:36` | `fit_gbox` |
| `work/tree_r1/student_pilot/ground_lifting.py:64` | `public_centres` |
| `work/tree_r1/student_pilot/ground_lifting.py:93` | `interior_depths` |
| `work/tree_r1/student_pilot/ground_lifting.py:107` | `depth_cut_keep` |
| `work/tree_r1/student_pilot/ground_lifting.py:117` | `lift_object` |
| `work/tree_r1/student_pilot/ground_lifting.py:183` | `render_ground` |
| `work/tree_r1/student_pilot/ground_lifting.py:199` | `gap_objects` |
| `work/tree_r1/student_pilot/ground_lifting.py:221` | `render_gap` |
| `work/tree_r1/student_pilot/ground_lifting.py:226` | `render_gaps` |
| `work/tree_r1/student_pilot/ground_lifting.py:243` | `OwnGeometryAdapter.__init__` |
| `work/tree_r1/student_pilot/ground_lifting.py:247` | `OwnGeometryAdapter.cam` |
| `work/tree_r1/student_pilot/ground_lifting.py:254` | `OwnGeometryAdapter.fov_of` |
| `work/tree_r1/student_pilot/ground_lifting.py:257` | `OwnGeometryAdapter._depth` |
| `work/tree_r1/student_pilot/ground_lifting.py:275` | `OwnGeometryAdapter.lift` |
| `work/tree_r1/student_pilot/ground_profiles.py:8` | `load_geometry` |
| `work/tree_r1/student_pilot/ground_profiles.py:25` | `build_profile` |
| `work/tree_r1/student_pilot/ground_profiles.py:34` | `export_values` |
| `work/tree_r1/student_pilot/ground_replay.py:11` | `pack_array` |
| `work/tree_r1/student_pilot/ground_replay.py:17` | `unpack_array` |
| `work/tree_r1/student_pilot/ground_replay.py:22` | `geometry_record` |
| `work/tree_r1/student_pilot/ground_replay.py:42` | `record_mask` |
| `work/tree_r1/student_pilot/ground_replay.py:49` | `restore_geometry` |
| `work/tree_r1/student_pilot/ground_replay.py:87` | `ReplayBackend.__init__` |
| `work/tree_r1/student_pilot/ground_replay.py:92` | `ReplayBackend.ground` |
| `work/tree_r1/student_pilot/ground_replay.py:100` | `ReplayBackend.gap` |
| `work/tree_r1/student_pilot/ground_sources.py:11` | `cache_phrase` |
| `work/tree_r1/student_pilot/ground_sources.py:20` | `native_gate` |
| `work/tree_r1/student_pilot/ground_sources.py:25` | `native_candidates` |
| `work/tree_r1/student_pilot/ground_sources.py:46` | `file_sha256` |
| `work/tree_r1/student_pilot/ground_sources.py:66` | `MaskProvider.__init__` |
| `work/tree_r1/student_pilot/ground_sources.py:72` | `MaskProvider.masks_for` |
| `work/tree_r1/student_pilot/ground_sources.py:78` | `NativeMDG.__init__` |
| `work/tree_r1/student_pilot/ground_sources.py:86` | `NativeMDG.bind_native_backend` |
| `work/tree_r1/student_pilot/ground_sources.py:89` | `NativeMDG.masks_for` |
| `work/tree_r1/student_pilot/ground_sources.py:105` | `CachedSAM3.__init__` |
| `work/tree_r1/student_pilot/ground_sources.py:119` | `CachedSAM3.proposals_for` |
| `work/tree_r1/student_pilot/ground_sources.py:125` | `CachedSAM3.selector_candidates` |
| `work/tree_r1/student_pilot/ground_sources.py:130` | `CachedSAM3.native_mask` |
| `work/tree_r1/student_pilot/ground_sources.py:141` | `TowerSAM3.__init__` |
| `work/tree_r1/student_pilot/ground_sources.py:150` | `TowerSAM3._detect` |
| `work/tree_r1/student_pilot/ground_sources.py:170` | `TowerSAM3.proposals_for` |
| `work/tree_r1/student_pilot/ground_sources.py:175` | `TowerSAM3.selector_candidates` |
| `work/tree_r1/student_pilot/ground_sources.py:178` | `TowerSAM3.native_mask` |
| `work/tree_r1/student_pilot/ground_sources.py:184` | `OwnProposals.__init__` |
| `work/tree_r1/student_pilot/ground_sources.py:191` | `OwnProposals.proposals_for` |
| `work/tree_r1/student_pilot/ground_sources.py:200` | `VerifyStub.__call__` |
| `work/tree_r1/student_pilot/ground_v3.py:16` | `same_object` |
| `work/tree_r1/student_pilot/ground_v3.py:35` | `GroundV3.__init__` |
| `work/tree_r1/student_pilot/ground_v3.py:115` | `GroundV3._memory_entry` |
| `work/tree_r1/student_pilot/ground_v3.py:120` | `GroundV3._claims_enabled` |
| `work/tree_r1/student_pilot/ground_v3.py:123` | `GroundV3._miss` |
| `work/tree_r1/student_pilot/ground_v3.py:126` | `GroundV3._resolve` |
| `work/tree_r1/student_pilot/ground_v3.py:203` | `GroundV3._score` |
| `work/tree_r1/student_pilot/ground_v3.py:209` | `GroundV3._select` |
| `work/tree_r1/student_pilot/ground_v3.py:251` | `GroundV3.query` |
| `work/tree_r1/student_pilot/ground_v3.py:254` | `GroundV3.begin_question` |
| `work/tree_r1/student_pilot/ground_v3.py:268` | `GroundV3.ground` |
| `work/tree_r1/student_pilot/ground_v3.py:298` | `GroundV3._emit` |
| `work/tree_r1/student_pilot/ground_v3.py:320` | `GroundV3.verify_request` |
| `work/tree_r1/student_pilot/ground_v3.py:334` | `GroundV3._verify_candidates` |
| `work/tree_r1/student_pilot/ground_v3.py:354` | `GroundV3.retry_verify` |
| `work/tree_r1/student_pilot/ground_v3.py:393` | `GroundV3.accept_verify` |
| `work/tree_r1/student_pilot/ground_v3.py:425` | `GroundV3.gap` |
| `work/tree_r1/student_pilot/live_instances314.py:13` | `ExactFrames.__init__` |
| `work/tree_r1/student_pilot/live_instances314.py:23` | `ExactFrames.has` |
| `work/tree_r1/student_pilot/live_instances314.py:24` | `ExactFrames.has_pose` |
| `work/tree_r1/student_pilot/live_instances314.py:33` | `ExactFrames.lift` |
| `work/tree_r1/student_pilot/live_instances314.py:43` | `ExactFrames.__getattr__` |
| `work/tree_r1/student_pilot/live_instances314.py:46` | `record_geometry` |
| `work/tree_r1/student_pilot/live_instances314.py:55` | `restore_recorded_geometry` |
| `work/tree_r1/student_pilot/live_instances314.py:66` | `unpack_mask` |
| `work/tree_r1/student_pilot/live_instances314.py:71` | `relift_instances` |
| `work/tree_r1/student_pilot/live_instances314.py:78` | `bridge_cut` |
| `work/tree_r1/student_pilot/live_instances314.py:84` | `components` |
| `work/tree_r1/student_pilot/live_instances314.py:114` | `query_instances` |
| `work/tree_r1/student_pilot/live_trace313.py:14` | `LiveSession.__init__` |
| `work/tree_r1/student_pilot/live_trace313.py:35` | `LiveSession.execute` |
| `work/tree_r1/student_pilot/live_trace313.py:39` | `LiveSession._room` |
| `work/tree_r1/student_pilot/live_trace313.py:55` | `LiveSession.bind_state` |
| `work/tree_r1/student_pilot/live_trace313.py:66` | `LiveSession._instances` |
| `work/tree_r1/student_pilot/live_trace313.py:96` | `entries` |
| `work/tree_r1/student_pilot/live_trace313.py:117` | `AuditSession.__init__` |
| `work/tree_r1/student_pilot/live_trace313.py:137` | `AuditSession.execute` |
| `work/tree_r1/student_pilot/live_trace313.py:141` | `AuditSession._room` |
| `work/tree_r1/student_pilot/live_trace313.py:153` | `AuditSession._instances` |
| `work/tree_r1/student_pilot/live_trace313.py:169` | `parse_response` |
| `work/tree_r1/student_pilot/live_trace313.py:238` | `replay` |
| `work/tree_r1/student_pilot/live_trace313.py:252` | `check_record` |
| `work/tree_r1/student_pilot/mdg_decode.py:14` | `decoder` |
| `work/tree_r1/student_pilot/mdg_decode.py:19` | `threshold` |
| `work/tree_r1/student_pilot/mdg_decode.py:29` | `PrefixCapture.__init__` |
| `work/tree_r1/student_pilot/mdg_decode.py:32` | `PrefixCapture.__enter__` |
| `work/tree_r1/student_pilot/mdg_decode.py:48` | `PrefixCapture.__exit__` |
| `work/tree_r1/student_pilot/mdg_decode.py:51` | `PrefixCapture.finish` |
| `work/tree_r1/student_pilot/mdg_decode.py:69` | `predict` |
| `work/tree_r1/student_pilot/mdg_decode.py:82` | `Backend.__init__` |
| `work/tree_r1/student_pilot/mdg_decode.py:91` | `Backend.query` |
| `work/tree_r1/student_pilot/mdg_decode.py:101` | `Backend.ground` |
| `work/tree_r1/student_pilot/mdg_decode.py:119` | `Backend.gap` |
| `work/tree_r1/student_pilot/mdg_decode.py:123` | `cached_gap` |
| `work/tree_r1/student_pilot/mdg_decode.py:135` | `ReplayBackend.__init__` |
| `work/tree_r1/student_pilot/mdg_decode.py:140` | `ReplayBackend.ground` |
| `work/tree_r1/student_pilot/mdg_decode.py:150` | `ReplayBackend.gap` |
| `work/tree_r1/student_pilot/native_selection.py:7` | `select` |
| `work/tree_r1/student_pilot/object_memory.py:37` | `ObjectSlot.finalize` |
| `work/tree_r1/student_pilot/object_memory.py:50` | `ClipMemory.__init__` |
| `work/tree_r1/student_pilot/object_memory.py:58` | `ClipMemory.bind` |
| `work/tree_r1/student_pilot/object_memory.py:63` | `ClipMemory.key` |
| `work/tree_r1/student_pilot/object_memory.py:67` | `ClipMemory.get` |
| `work/tree_r1/student_pilot/object_memory.py:73` | `ClipMemory.put` |
| `work/tree_r1/student_pilot/s1_grounding.py:14` | `default_policy` |
| `work/tree_r1/student_pilot/s1_grounding.py:23` | `candidate_names` |
| `work/tree_r1/student_pilot/s1_grounding.py:34` | `build_backend` |
| `work/tree_r1/student_pilot/s1_grounding.py:41` | `_build_backend` |
| `work/tree_r1/student_pilot/scene_state.py:8` | `digest` |
| `work/tree_r1/student_pilot/scene_state.py:13` | `normalize_name` |
| `work/tree_r1/student_pilot/scene_state.py:32` | `FrameMap.__post_init__` |
| `work/tree_r1/student_pilot/scene_state.py:54` | `FrameMap.require` |
| `work/tree_r1/student_pilot/scene_state.py:65` | `SceneState.__post_init__` |
| `work/tree_r1/student_pilot/scene_state.py:72` | `SceneState.identity` |
| `work/tree_r1/student_pilot/scripted_calls.py:9` | `validate_reference` |
| `work/tree_r1/student_pilot/scripted_calls.py:52` | `ReferenceChoice.__init__` |
| `work/tree_r1/student_pilot/scripted_calls.py:64` | `ReferenceChoice.choose` |
| `work/tree_r1/student_pilot/scripted_calls.py:74` | `ReferenceChoice.check_complete` |
| `work/tree_r1/student_pilot/svp_stages.py:10` | `footprint` |
| `work/tree_r1/student_pilot/svp_stages.py:39` | `propagate` |
| `work/tree_r1/student_pilot/svp_stages.py:63` | `NativePresence.__init__` |
| `work/tree_r1/student_pilot/svp_stages.py:67` | `NativePresence.bind_native_backend` |
| `work/tree_r1/student_pilot/svp_stages.py:71` | `NativePresence.__call__` |
| `work/tree_r1/student_pilot/svp_stages.py:90` | `RescuePass.validate` |
| `work/tree_r1/student_pilot/svp_stages.py:105` | `SVPStages.__init__` |
| `work/tree_r1/student_pilot/svp_stages.py:117` | `SVPStages.config` |
| `work/tree_r1/student_pilot/svp_stages.py:125` | `SVPStages.prior` |
| `work/tree_r1/student_pilot/svp_stages.py:133` | `SVPStages.visible` |
| `work/tree_r1/student_pilot/svp_stages.py:137` | `SVPStages.propagate` |
| `work/tree_r1/student_pilot/tower_read.py:27` | `validate_pose_source` |
| `work/tree_r1/student_pilot/tower_read.py:32` | `_numpy` |
| `work/tree_r1/student_pilot/tower_read.py:36` | `_anchors` |
| `work/tree_r1/student_pilot/tower_read.py:47` | `_lm_indices` |
| `work/tree_r1/student_pilot/tower_read.py:71` | `TowerState.__post_init__` |
| `work/tree_r1/student_pilot/tower_read.py:100` | `TowerState.from_npz` |
| `work/tree_r1/student_pilot/tower_read.py:110` | `TowerState.validate_batch` |
| `work/tree_r1/student_pilot/tower_read.py:120` | `TowerState.scaled_pose9` |
| `work/tree_r1/student_pilot/tower_read.py:130` | `g3t_to_c1_pose9` |
| `work/tree_r1/student_pilot/tower_read.py:136` | `_hash` |
| `work/tree_r1/student_pilot/tower_read.py:145` | `FrozenG3TTower.__init__` |
| `work/tree_r1/student_pilot/tower_read.py:166` | `FrozenG3TTower._load` |
| `work/tree_r1/student_pilot/tower_read.py:198` | `FrozenG3TTower.run` |
| `work/tree_r1/student_pilot/tower_read.py:295` | `attach_tower` |
| `work/tree_r1/student_pilot/tower_read.py:302` | `prepare_tower` |
| `work/tree_r1/student_pilot/tower_read.py:311` | `apply_tower` |
| `work/tree_r1/student_pilot/tower_scale.py:9` | `estimate_scale` |
| `work/tree_r1/student_pilot/tower_scale_rule.py:4` | `estimate` |
| `work/tree_r1/student_pilot/trace_format313.py:13` | `bind_state` |
| `work/tree_r1/student_pilot/trace_format313.py:17` | `active` |
| `work/tree_r1/student_pilot/trace_format313.py:19` | `extra_tail` |
| `work/tree_r1/student_pilot/trace_format313.py:21` | `respond` |
| `work/tree_r1/student_pilot/trace_format313.py:35` | `row` |
| `work/tree_r1/student_pilot/trace_format313.py:43` | `bind_generate` |
| `work/tree_r1/trace_format/box_v313.py:33` | `number` |
| `work/tree_r1/trace_format/box_v313.py:40` | `box` |
| `work/tree_r1/trace_format/box_v313.py:51` | `sampled_box_512` |
| `work/tree_r1/trace_format/box_v313.py:62` | `grid_points` |
| `work/tree_r1/trace_format/box_v313.py:74` | `box_grid_5cm` |
| `work/tree_r1/trace_format/box_v313.py:79` | `camera_gap` |
| `work/tree_r1/trace_format/box_v313.py:83` | `measure` |
| `work/tree_r1/trace_format/box_v313.py:89` | `public_fields` |
| `work/tree_r1/trace_format/box_v313.py:103` | `tilted_public_fields` |
| `work/tree_r1/trace_format/box_v313.py:121` | `yaw_box` |
| `work/tree_r1/trace_format/box_v313.py:126` | `serialize` |
| `work/tree_r1/trace_format/box_v313.py:139` | `parse` |
| `work/tree_r1/trace_format/box_v313.py:160` | `audit_box` |
| `work/tree_r1/trace_format/box_v313.py:164` | `split_instances` |
| `work/tree_r1/trace_format/box_v313.py:182` | `BoxRegistry.__init__` |
| `work/tree_r1/trace_format/box_v313.py:185` | `BoxRegistry.invalidate` |
| `work/tree_r1/trace_format/box_v313.py:188` | `BoxRegistry.ingest` |
| `work/tree_r1/trace_format/box_v313.py:220` | `BoxRegistry.ingest_metric` |
| `work/tree_r1/trace_format/box_v313.py:230` | `BoxRegistry.audit_labels` |
| `work/tree_r1/trace_format/box_v313.py:234` | `BoxRegistry.gap` |
| `work/tree_r1/trace_format/box_v313.py:258` | `cam_gap_body` |
| `work/tree_r1/trace_format/box_v313.py:282` | `camera_centre_f1` |
| `work/tree_r1/trace_format/box_v313.py:299` | `_gap_audit` |
| `work/tree_r1/trace_format/box_v313.py:314` | `replay_audit` |
| `work/tree_r1/trace_format/box_v313.py:374` | `render_camera` |
| `work/tree_r1/trace_format/box_v313.py:377` | `_disabled_render_camera` |
| `work/tree_r1/trace_format/box_v313.py:423` | `in_f1` |
| `work/tree_r1/trace_format/box_v313.py:436` | `FittedBoxProvider.__init__` |
| `work/tree_r1/trace_format/box_v313.py:437` | `FittedBoxProvider.__call__` |
| `work/tree_r1/trace_format/box_v313.py:448` | `FusedBoxProvider.__init__` |
| `work/tree_r1/trace_format/box_v313.py:450` | `FusedBoxProvider.__call__` |
| `work/tree_r1/trace_format/box_v313.py:460` | `vote_points` |
| `work/tree_r1/trace_format/box_v313.py:474` | `_finite` |
| `work/tree_r1/trace_format/box_v313.py:487` | `PolicyBoxProvider.__init__` |
| `work/tree_r1/trace_format/box_v313.py:489` | `PolicyBoxProvider._cut` |
| `work/tree_r1/trace_format/box_v313.py:492` | `PolicyBoxProvider._fit` |
| `work/tree_r1/trace_format/box_v313.py:498` | `PolicyBoxProvider.__call__` |
| `work/tree_r1/trace_format/box_v313.py:506` | `PolicyBoxProvider.gap_box` |
| `work/tree_r1/trace_format/box_v313.py:514` | `provider_for` |
| `work/tree_r1/trace_format/box_v313.py:530` | `AnnotationBoxProvider.__call__` |
| `work/tree_r1/trace_format/box_v313.py:537` | `ground` |
| `work/tree_r1/trace_format/box_v313.py:618` | `render` |
| `work/tree_r1/trace_format/box_v313.py:671` | `fit_gbox` |
| `work/tree_r1/trace_format/box_v313.py:704` | `fit_gbox_full` |
| `work/tree_r1/trace_format/program_errors.py:3` | `ProgramRefusal.__init__` |
| `work/tree_r1/trace_format/room_v314.py:23` | `RoomRefusal.__init__` |
| `work/tree_r1/trace_format/room_v314.py:28` | `_finite` |
| `work/tree_r1/trace_format/room_v314.py:33` | `_frames` |
| `work/tree_r1/trace_format/room_v314.py:53` | `_dense` |
| `work/tree_r1/trace_format/room_v314.py:125` | `sample` |
| `work/tree_r1/trace_format/room_v314.py:145` | `measure` |
| `work/tree_r1/trace_format/room_v314.py:149` | `from_points` |
| `work/tree_r1/trace_format/room_v314.py:204` | `format_result` |
| `work/tree_r1/trace_format/room_v314.py:215` | `parse_response` |

## Portrait audit

The fixed-mask canvases in `student_pilot/routed_features.py:18`, `ofs/core.py:51` and `verifykit/export.py:32` distort portrait aspect. Portrait and landscape square-mask fixture extents are in `work/build7/proofs/targeted_final/portrait/RESULT.json`. The GF-1 square-pad path preserves aspect, but padded coordinates still require the existing ROI mapping. The native student processor normally uses aspect-aware resize; the absent production processor configuration prevents full qualification. No RGB source population was inspected, so each bound slice has an unknown portrait share.

The complete resize-site audit is `work/build7/proofs/audit/RESIZE_AUDIT.json`. Entries marked “requires transform-context review” remain open; the audit did not establish every resize as safe. No mask coordinate change was made because row-byte parity was not proved.

| Resize location | Portrait assessment |
|---|---|
| `work/tree_r1/verifykit/io.py:84` | requires transform-context review |
| `work/tree_r1/verifykit/export.py:32` | True |
| `work/tree_r1/verifykit/prepare.py:104` | requires transform-context review |
| `work/tree_r1/verifykit/render.py:33` | requires transform-context review |
| `work/tree_r1/verifykit/render.py:34` | requires transform-context review |
| `work/tree_r1/verifykit/model.py:73` | requires transform-context review |
| `work/tree_r1/ofs/core.py:51` | True |
| `work/tree_r1/ofs/core.py:53` | True |
| `work/tree_r1/ofs/core.py:54` | True |
| `work/tree_r1/ofs/core.py:60` | True |
| `work/tree_r1/trace_format/ground_v313.py:373` | True |
| `work/tree_r1/rk/resample.py:32` | True |
| `work/tree_r1/rk/gtmask.py:34` | True |
| `work/tree_r1/rk/sam3mask.py:44` | True |
| `work/tree_r1/rk/sam3mask.py:83` | True |
| `work/tree_r1/student_pilot/verify_pass.py:119` | requires transform-context review |
| `work/tree_r1/student_pilot/routed_features.py:23` | True |
| `work/tree_r1/student_pilot/sam3_tower.py:106` | requires transform-context review |
| `work/tree_r1/student_pilot/g3t_online.py:377` | requires transform-context review |
| `work/tree_r1/student_pilot/g3t_online.py:389` | requires transform-context review |
| `work/tree_r1/student_pilot/grounding_head.py:183` | requires transform-context review |
| `work/tree_r1/student_pilot/grounding_head.py:188` | requires transform-context review |
| `work/tree_r1/student_pilot/mdg_eval.py:576` | requires transform-context review |
| `work/tree_r1/student_pilot/c1r_dense.py:304` | requires transform-context review |
| `work/tree_r1/student_pilot/mdg_train.py:225` | requires transform-context review |
| `work/tree_r1/student_pilot/clean_media.py:110` | requires transform-context review |
| `work/tree_r1/student_pilot/grounding_targets.py:215` | requires transform-context review |
| `work/tree_r1/student_pilot/reread.py:167` | requires transform-context review |
| `work/tree_r1/student_pilot/mask_grounding_head.py:77` | requires transform-context review |
| `work/tree_r1/student_pilot/mask_grounding_head.py:196` | requires transform-context review |
| `work/tree_r1/student_pilot/mask_grounding_head.py:212` | requires transform-context review |
| `work/tree_r1/student_pilot/mask_grounding_head.py:213` | requires transform-context review |
| `work/tree_r1/student_pilot/mask_grounding_head.py:276` | requires transform-context review |
| `work/tree_r1/student_pilot/c1r_ref.py:77` | requires transform-context review |
| `work/tree_r1/student_pilot/point_depth_head.py:198` | requires transform-context review |
| `work/tree_r1/student_pilot/routed_candidates.py:51` | True |
| `work/tree_r1/student_pilot/routed_candidates.py:53` | True |
| `work/tree_r1/student_pilot/routed_candidates.py:54` | True |
| `work/tree_r1/student_pilot/routed_candidates.py:60` | True |
| `work/tree_r1/student_pilot/tower_read.py:237` | requires transform-context review |
| `work/tree_r1/tools/g3t_patch_grid_store.py:223` | requires transform-context review |
| `work/tree_r1/tools/g3t_camera_sidecar_store.py:272` | requires transform-context review |
| `work/tree_r1/student_pilot/benchmark_eval/prepare.py:324` | requires transform-context review |
| `work/tree_r1/student_pilot/orchard_eval/prepare.py:326` | requires transform-context review |
| `work/tree_r1/student_pilot/g3t_vendor/vggt/heads/dpt_head.py:479` | requires transform-context review |
| `work/tree_r1/student_pilot/g3t_vendor/vggt/heads/dpt_head.py:484` | requires transform-context review |
| `work/tree_r1/student_pilot/g3t_vendor/vggt/layers/vision_transformer.py:204` | requires transform-context review |
| `work/tree_r1/student_pilot/g3t_vendor/vggt/utils/load_fn.py:77` | requires transform-context review |
| `work/tree_r1/student_pilot/g3t_vendor/vggt/utils/load_fn.py:169` | requires transform-context review |

## Stop path

S1 wrote the host-kit stop file while its sandbox used a separate staged kit; S1 also did not export the K3 path that ranks poll. The host path is at `launch_s1/b/r.sh:12`; the added staged-file write is at `launch_s1/b/r.sh:17`, and the sandbox poll-path export is at `launch_s1/b/r.sh:58`. The rank checks that request at the step boundary in `student_pilot/carrier_c1_run.py:2378`. `work/build7/proofs/review/STOP_PATH.json` records the current chain. The real extracted shell trap and native poll pass; `work/build7/proofs/stop/RESULTS.json` records both stop-file SHA256 values.

Gloo initialization failed with “Cannot resolve 127.0.0.1 to a (local) address” (`work/build7/proofs/stop/RESULTS.json`). I did not retry or bypass that environment restriction. There is no multi-rank end slot or corresponding hash. A real multi-rank fallback export remains unproved.

The separate single-rank fallback ran the native optimizer loop, checkpoint/export writers and artifact reader. Its end-slot path and digest are `{"path": "/scratch/jjyeung/orch_n30/tree_rebuild_w/work/build7/proofs/final_targeted/stop_fallback/m1/artifact.json", "sha256": "36cc1787cd3ea6d44d8d5b7a2cfe5ba76bc2648dc7f144f67e59cecf337fa384"}`; the checkpoint is `{"path": "/scratch/jjyeung/orch_n30/tree_rebuild_w/work/build7/proofs/final_targeted/stop_fallback/checkpoint_000001_aeebf46707444da2b303d3f83d17e72c/complete.json", "sha256": "30745d19d76d9fbdffe0ee5cc1d19773a618f5ae23d17323646314e8509bb498"}` (`work/build7/proofs/final_targeted/stop_fallback/RESULT.json`). It uses synthetic pose batches plus one-rank collective and FSDP publication stand-ins. It does not meet the GPU-boundary-only requirement for the full producer/wrapper chain.

## For the second review

- Review the both-path build-loop/type gate and sampler separately. Check preserved policies, per-item form identity, missing grammars, native preparation binding and exact minority quotas. The shared grammar authority remains byte-identical (`work/build7/proofs/audit/AUTHORITY_HASHES.json`).
- Check the legacy direct-source entry before using it with the new policy: `student_pilot/carrier_c1_routing.py:888` constructs an empty-think row, and its direct-source loop calls that constructor. This path is not qualified for the requested concrete GT traces. The current bound-row route through R2 admission does not establish parity for that separate builder entry.
- Review the cache rebase and its numerical limits. Every hunk disposition is in `work/build7/PATCH_HUNKS.json`; BF16 gradient parity fails the original tolerance. Confirm the off path and FP32 launch restriction before enabling the option.
- Review faithful-row all-reduced refusals and the identity gate. The native tiny OFF proof passes; full scheduled-sampling encoder parity and bound-row identity remain unqualified. No independent review was performed: the build explicitly forbids another agent.
- Review unresolved product computations against EAT, and the manifest’s missing full production read closure. No acceptance claim follows from attaching module names or a manifest.
- Review every remaining suite regression and CPU gap before changing GO. `work/build7/SUITE_COMPARISON.json`, `GAPS.json` and `BUILD6_DISPOSITION.json` are the authoritative lists.

## Limits and delivery state

Final artifact hashes and storage check: {"tree_seal": "26a635fc34aa97ac2909985ca4c1e1007c03e621ab95742d2a7c93a7b282b052", "tree_files": 878, "storage_bytes": {"lane": 1831846000, "tmp": 18997935}, "scratch_free_bytes": 586267578368} (`work/build7/FINAL_VERIFICATION.json`).

Not checked: real staging bytes on Orchard/GCS, the selected init, full stores, complete alias overlap, production processor values, real frame portrait share, GPU capacity or timing, real distributed stop/export, every formatter, every long-frame reader, full trained-module closure, a production EAT read, or an independent review. No launch, remote call, checkpoint copy, full-store materialization, Git, SSH, GPU or other agent was used. The package and kits are review artifacts; GO remains false.
