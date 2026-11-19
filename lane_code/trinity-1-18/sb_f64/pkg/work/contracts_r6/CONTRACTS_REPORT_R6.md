The r6 packet closes the interdiff findings. Both patched trees pass the full suite, OFF preserves sealed output bytes, and ON changes pass the strict row comparison. [application proof](/scratch/jjyeung/orch_n30/contracts_rebuild/out/APPLY_PROOF_R6.json); [parity](/scratch/jjyeung/orch_n30/contracts_rebuild/out/ROW_FAMILY_PARITY_R6.json).

Each patched tree passes 202 tests. All 15 new regression cases fail on r5 and pass on r6. [suite evidence](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json); [regression evidence](/scratch/jjyeung/orch_n30/contracts_rebuild/out/R5_REGRESSION_PROOF_R6.json).

Mutation tests kill 87 mutants and verify 4 equivalent mutants, including every r5 mutant. Each run uses the full suite with early exit. [mutation evidence](/scratch/jjyeung/orch_n30/contracts_rebuild/out/MUTATION_R6.json).

Each row arm renders 360 rows; OFF equals base byte for byte. ON admits 354 and defers 6 synthetic bare-gap rows. [row evidence](/scratch/jjyeung/orch_n30/contracts_rebuild/out/ROW_FAMILY_PARITY_R6.json).

The POOL audit admits 195564 source records and defers 0. It finds 0 bare-gap records. [POOL evidence](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_ROW_AUDIT_R6.json).

The real G3T replay covers 152 captures with 0 failed assertions. [capture inventory](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r6/CAPTURE_INVENTORY.json); [replay evidence](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r6/REAL_GEOMETRY_REPLAY.json).

| Item | Current change / decision | Test | Result and source |
|---|---|---|---|
| F-1 | Choose horizontal basis and cached poses by the query epoch and heading threshold. Decode construction can precede the session context. | test_basis_uses_query_context | PASS; [suite](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json) |
| F-2 | Initialize the live provider and registries inside the backend context; execute and replay under that same context. | test_live_provider_uses_backend_epoch | PASS; [suite](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json) |
| L-a | Attempt the contracts import at registry construction; fall back to sealed only on ImportError. Standalone imports and construction remain supported. | test_generator_import_order; test_standalone_generator_imports; test_standalone_construction_fallback | PASS; [suite](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json) |
| L-b | Copy only containers changed by alias merging; share mask payloads and preserve the caller cache. | test_cache_view_shares_mask_payload_without_mutation; test_cache_lookup_preserves_caller | PASS; [suite](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json) |
| L-c | Return None for a binding dict without phrases so the missing-manifest guard fires. | test_missing_manifest_phrases | PASS; [suite](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json) |
| L-d | Render pose, move and turn from structured arguments in every heading state. | test_rerender_head_arguments | PASS; [suite](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json) |
| L-e | Keep runtime batch/cache phrases ahead of row declarations; use a pinned manifest only as fallback. | test_shared_binding_served_or_deferred; test_build_defers_one_row_and_keeps_clean_row | PASS; [suite](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json) |
| L-f | Reject changed dictionary keys, leaf types and non-string leaves. Validate documented private audit additions and derived offsets separately. | test_strict_row_structure; row_families_r6/validate_evidence.py | PASS; [row comparison](/scratch/jjyeung/orch_n30/contracts_rebuild/out/ROW_FAMILY_PARITY_R6.json) |
| L-2c | Keep bare-gap deferral under ON: 6 synthetic rows defer; 0 real POOL rows use the form. [row evidence](/scratch/jjyeung/orch_n30/contracts_rebuild/out/ROW_FAMILY_PARITY_R6.json); [POOL evidence](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_ROW_AUDIT_R6.json) | test_legacy_gap_off_grammar; test_legacy_scalar_gap_audit | PASS; [suite](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json) |

The mask cache defines the runtime competition universe. Batch cache phrases and persisted batch cache phrases win; row candidate phrases precede row cache phrases and row manifests. A separately pinned manifest supplies a missing binding. [resolver](/scratch/jjyeung/orch_n30/contracts_rebuild/work/src_r6/student_pilot/phrases.py).

OwnGeometry selects its basis and pose cache at use. Ground lifting also chooses its metric basis at use. The decode response context follows the live session; the live session pins provider construction and execution to its backend. Generator registry construction checks import availability explicitly. Existing class API, mixed-point, provider and replay regressions remain covered. [heading inventory](/scratch/jjyeung/orch_n30/contracts_rebuild/out/HEADING_DEPENDENCE_R6.md); [reviewer probes](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REVIEW_C5_PROBES_R6.json).

The vertical-reference test checks ON adapter parity separately from the sealed OFF error. It does not use an ON basis as an OFF oracle. [test adjustment](/scratch/jjyeung/orch_n30/contracts_rebuild/out/FINAL_TEST_RESULTS_R6.json).

Bare-gap rows still defer under ON. The legacy sealed session can emit bare scalar gaps; the POOL count does not imply that every runtime forbids them. [legacy emitter](/scratch/jjyeung/orch_n30/contracts_rebuild/work/base/work/base/tree_b01ce449/trace_format/ground_v312.py); [audit](/scratch/jjyeung/orch_n30/contracts_rebuild/out/REAL_ROW_AUDIT_R6.json).

RGB inputs and printed numerical observations keep their existing paths. The gravity guard and threshold contract are unchanged. CPU fixtures and synthetic replay masks verify software contracts; they do not measure model quality or establish metric calibration for raw tower units. [guard integrity](/scratch/jjyeung/orch_n30/contracts_rebuild/out/PACKET_INTEGRITY_R6.json); [replay scope](/scratch/jjyeung/orch_n30/contracts_rebuild/out/real_replay_r6/REAL_GEOMETRY_REPLAY.json).

No project-history statements are retained. The r5/r6 labels identify the requested controlled regression comparison.
