# Build 16

**GO=false. N’s new row inputs, counting guard, census, resumed sampler and relocated handover reader are implemented. Production qualification is incomplete.** The single successful native production-mode fixture requested in step 4 has not been demonstrated. The component proofs below do not replace it. Sources: `work/build16/STATUS.md`, `work/build16/proofs/census/`, `work/build16/proofs/final_focused/TESTS.json`.

## Initialization and production blockers

N does not need P’s checkpoint state shards to initialize from the export. It does still need the build-15 `routing_vocabulary` witness (`v.json`). Reconstructing that witness needs the model manifest named by P’s preparation, pinned tokenizer/config metadata and P’s parent artifact. Native trainable-group verification also reads the model manifest and `config.json`. These files are outside the direct persistence closure produced by the unchanged P receipt producer. Their availability outside P’s step-400 tmpfs cannot be established without a real export. If they exist only there, N’s full initialization is blocked. No actual tmpfs-only filename has been established from supplied exports. Sources: `work/tree_r1/launch_r1/p_opener_witness.py`, `work/tree_r1/student_pilot/r1_handover.py:donor_meta_model`, `work/build16/proofs/operator/OPERATOR.md`.

The initialization-boundary fixture verifies this dependency: metadata handover admits the persisted export, while the native topology reader refuses with `P_EXPORT_TOPOLOGY_METADATA_UNVERIFIED` when P’s model manifest is unavailable on N. The manifest’s hash is absent from the unchanged receipt’s direct pin list. Source: `work/build16/proofs/init_boundary/b16/persisted_400/INIT_BOUNDARY.json`. This fixture proves the missing dependency; it does not prove a complete successful host job.

The complete K1 authority and alias maps are absent. The local audit removes known positives and refuses to certify unknown overlap. The production mode requires a complete pinned room audit; the local subset cannot satisfy that gate. Production frame stores, the operator’s real P export and its trusted ledger receipt were not supplied. Full-model CPU memory fit and BF16 parity were not measured. Sources: `work/build16/INPUTS.json`, `work/build16/proofs/operator/STAGING.json`, `work/tree_r1/launch_r1/production_proof.py`.

The mode invoked with the actual local N kit-input config returns `R1_PROOF_NATIVE_ROUTING_REQUIRED`: the frame host has not yet supplied the native routing manifests in its runtime config. The incomplete local room audit remains a further unmet prerequisite. The mode stops before reading production rows or loading weights. Source: `work/build16/proofs/init_boundary/b16/real_room_boundary/RESULT.json`.

## Changes and closure

| Requirement | Status | Evidence |
|---|---|---|
| Pinned N sources, merged extent receipt, removal order | Closed | inputs/config.json; inputs/row_sources.json; proofs/preservation/RESULT.json |
| Complete K1/R0/division certification | Blocked: full K1 authority/aliases absent; exact R0 and canonical division checks run | INPUTS.json; inputs/s.json; proofs/census/CENSUS.json |
| Procedure-only counting card and admission guard | Closed | inputs/CARD.md; inputs/mix.json; proofs/census/CLASSIFIER.json |
| Real v7 and slice census, producer binding, allocation and resumed plans | Closed within declared frame-host substitution; full camera/pose/pointing census blocked | proofs/census/CENSUS.json; PLAN_RUN.json; host_boundary.json |
| Native training text examples | Closed for available nonempty VQA/slice cells; camera traces blocked | proofs/traces/INDEX.json; proofs/traces/*.jsonl |
| Separate q mode and opaque CPU operator packet | Blocked qualification; implementation and packet supplied | proofs/operator/; KIT_RESULT.json; work/tree_r1/launch_r1/production_proof.py |
| One complete native production-mode CPU fixture | Blocked qualification: component tests only; no successful end-to-end fixture | proofs/final_focused/TESTS.json; DELTA_COVERAGE.json |
| Persisted-metadata handover at P milestones; absent state shards recorded | Closed in synthetic native export fixtures; real export blocked | proofs/final_focused/b16/; proofs/edges/TESTS.json |
| Final N config/preparation handover mapping | Closed in boundary fixtures; full admission chain unproven | tests/test_r1_build16.py:test_final_preparation_handover_binding |
| P receipt producer and collector unchanged | Closed: entire file byte-equal to build 15 | proofs/operator/P_PRODUCER_EQUALITY.json |
| Exact-JSON runtime audit | Closed; only test compares independently recomputed generator outputs | proofs/float/RESULT.json |
| Mutations, packet, frozen changed group, reseal and fresh kits | Closed for observed scope; unavailable groups and coverage gaps explicit | proofs/mutations/RESULT.json; SUITE_RUNS.json; DELTA_COVERAGE.json; KIT_RESULT.json |

Evidence paths in this table are under `work/build16/` unless they explicitly begin with `work/` or `tests/`; test source paths are relative to `work/tree_r1/`.

## Pinned inputs and exclusions

| Input | SHA-256 |
|---|---|
| v7: `/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite` | `210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443` |
| absolute_distance: `/scratch/jjyeung/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl` | `aedd3b54b913fd416b8daa53f022c86d1b3d98259f3c5e1a479e8bde528449d9` |
| recovery: `/scratch/jjyeung/n30_mirror/rows_r1/out/recovery_v3/rows.jsonl` | `58389a67f9a5b51abbc06e5953937b35541ef5effc4e70e6a35092d14f288473` |
| units: `/scratch/jjyeung/n30_mirror/rows_r1/out/vehN_units/repaired/rows_slice.jsonl` | `aa1432cde2aa3612e0d0e287c94aaa0aeb37dc175485a3ad044bca71f3e5ce9c` |

The filtered distance source and merged extent receipt retain their supplied pins in `inputs/row_sources.json` and `inputs/config.json`. The source list order is inherited, followed by the N-side known-positive list `s.json`, the original `n.json` second to last, and `z.json` last. The original list has 601 rows; z has 17,879 rows. Sources: `work/build16/proofs/preservation/RESULT.json`, `work/build16/proofs/census/CLASSIFIER.json`.

The R0 cache exactly matches `bdb5d402...` and contains 372 rooms. The K1 substitute is the pinned pool `K1_DROP.json`, source-QID twins and canonical capture identities. It is a positive-hit subset, not the full 50-room authority. The field `known_k1_rooms` contains capture identifiers, not a count of authoritative physical rooms. Sources: `work/build16/INPUTS.json`, `work/build16/inputs16.py`.

| Slice | Known K1 hits | R0 hits | Outside division train scenes | Newly removed after intake |
|---|---:|---:|---:|---:|
| absolute_distance | 0 | 0 | 0 | 0 |
| recovery | 21 | 0 | 0 | 17 |
| units | 262 | 0 | 0 | 262 |

Source: `work/build16/INPUTS.json` and `proofs/census/CENSUS.json`. All reported hits are in pinned `inputs/s.json` with their row key and reason. Recovery has 21 known positives, of which 4 already fail intake; the list therefore removes 17 additional admitted rows. Units loses 262 rows. Distance has no known-positive hit. The three slices have no unknown canonical provenance in this narrow check; missing full K1 membership still prevents a clean certification. The v7 check is report-only: no known K1/R0 hits were found, but 160,634 rows lack canonical membership resolution. Unknown is not a pass.

## Census and count changes

| VQA cell | Previous eligible | Current eligible | Removal-list refusals | Reader refusals |
|---|---:|---:|---:|---:|
| appearance_order | 27587 | 27587 | 204 | 0 |
| box_3d | 3813 | 3813 | 0 | 0 |
| camera_object_rel_distance_v1 | 1930 | 1930 | 21 | 0 |
| camera_object_rel_distance_v2 | 1957 | 1957 | 26 | 0 |
| camera_object_rel_distance_v3 | 1978 | 1978 | 20 | 0 |
| counting | 11295 | 2617 | 8749 | 0 |
| direction | 49901 | 49901 | 0 | 0 |
| facing_pairs | 43469 | 43469 | 0 | 0 |
| first_seen_frame | 6985 | 6985 | 91 | 0 |
| object_object_left_right | 1978 | 1978 | 20 | 0 |
| object_object_near_far | 1982 | 1982 | 18 | 0 |
| object_object_up_down | 1974 | 1974 | 22 | 0 |
| object_size | 9778 | 9778 | 0 | 0 |
| relative_distance | 20659 | 20659 | 0 | 6 |
| room_size | 425 | 425 | 6 | 0 |
| route_planning | 8894 | 8894 | 0 | 0 |
| totals | 9201 | 0 | 9303 | 0 |

Sources: previous `work/build14/proofs/census/CENSUS.json` (the census retained by build 15), current `work/build16/proofs/census/CENSUS.json`. The v7 read count is 204,413; 18,480 list removals and 6 unchanged Unicode reader refusals leave 185,927 rows. Counting falls from 11,295 to 2,617 because z removes 8,678 list-form rows. Totals falls from 9,201 to zero. Every other eligible VQA count is unchanged.

| Slice | Read | Requested pre-K1 reference | Current | Refusal reasons |
|---|---:|---:|---:|---|
| recovery | 994 | 777 | 760 | filter:remove_files: 17; intake:R2 fallback calls again after a failed response: 156; intake:excluded:eval_rooms: 61 |
| absolute_distance | 8315 | 7805 | 7805 | intake:excluded:eval_rooms: 510 |
| units | 8577 | 8067 | 7805 | filter:remove_files: 262; intake:excluded:eval_rooms: 510 |

Source: `work/build16/proofs/census/CENSUS.json`; pre-K1 reference: the build brief and native intake totals in that file. Distance remains 7,805 of 8,315. Relative to build 15’s retained smaller-pool count of 1,476, it increases because this build binds the full pool. Recovery changes from 777 to 760 and units from 8,067 to 7,805 solely because of the additional known K1 exclusions. Sources: `work/build14/proofs/census/CENSUS.json`, `work/build16/INPUTS.json`.

The census streams the real rows through the native reader and producer, with routing materialization retained only in memory. Frame metadata and canonical coverage substitute for unavailable frame-host inputs; missing FPS uses labelled GUESS 24. Camera, pose and pointing populations use synthetic host offsets with the previous counts. They are not real-store census results. Sources: `work/build16/census16.py`, `work/build16/proofs/census/host_boundary.json`.

## Counting guard and allocation

The port matches the reference classifier on every z row found in v7: FS_LIST=6636, FS_LIST_REGION=2042, TOTALS=1239, TOTALS_REGION=7962. Named admission failures are `R1_COUNTING_LIST_FORM_REFUSED`, `R1_TOTALS_ROW_REFUSED`, and `R1_COUNTING_PROCEDURE_REQUIRED`. Dropping z admits a forbidden example through the remaining filters and then triggers the producer guard. Sources: `work/build16/proofs/census/CLASSIFIER.json`, `work/tree_r1/student_pilot/r1_counting.py`, `tests/test_r1_build16.py:test_producer_refuses_without_z`.

Counting is floor(4 × 2,617 / 1,000 × 100) / 100 = **10.46** rows per step. Totals is **0**. Direction becomes 32.89 + 10.87 + 3.39 − 10.46 = **36.69**. Absolute distance stays **15.6**, below its **31.22** ceiling, so no cut or camera refill occurs. Every other requested cell and `weight_scale=0.04` stays unchanged. This applies C′’s procedure-only rule while preserving N’s zero room quota; P’s different room allocation does not change N’s card. Sources: `work/build16/inputs/CARD.md`, `inputs/mix.json`, `proofs/census/PLAN_RUN.json`; the supplied `inputs/count/CPRIME.md` is referenced by `inputs16.py`.

| Cell | Eligible | Ceiling | Quota | Mean | Min | Max | Total draws | Largest repeat | Resume 400 first | Resume 600 first |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| absolute_distance | 7805 | 31.22 | 15.6 | 15.6 | 15 | 16 | 15600 | 2 | 16 | 16 |
| appearance_order | 27587 | 110.348 | 14.42 | 14.42 | 14 | 15 | 14420 | 1 | 14 | 14 |
| box_3d | 3813 | 15.252 | 1.82 | 1.82 | 1 | 3 | 1820 | 1 | 2 | 2 |
| camera_displacement | 14020 | 56.08 | 17.42 | 17.42 | 17 | 18 | 17420 | 2 | 17 | 17 |
| camera_movement_direction | 12260 | 49.04 | 15.15 | 15.15 | 14 | 16 | 15150 | 2 | 15 | 15 |
| camera_object_abs_distance | 0 | 0.0 | 0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| camera_object_rel_distance_v1 | 1930 | 7.72 | 2 | 2.0 | 2 | 2 | 2000 | 2 | 2 | 2 |
| camera_object_rel_distance_v2 | 1957 | 7.828 | 2 | 2.0 | 2 | 2 | 2000 | 2 | 2 | 2 |
| camera_object_rel_distance_v3 | 1978 | 7.912 | 2 | 2.0 | 2 | 2 | 2000 | 2 | 2 | 2 |
| camera_rotation | 9143 | 36.572 | 11.96 | 11.96 | 11 | 13 | 11960 | 2 | 12 | 12 |
| counting | 2617 | 10.468 | 10.46 | 10.46 | 10 | 11 | 10460 | 4 | 10 | 10 |
| direction | 49901 | 199.604 | 36.69 | 36.69 | 36 | 37 | 36690 | 1 | 37 | 37 |
| facing_pairs | 43469 | 173.876 | 18.17 | 18.17 | 17 | 19 | 18170 | 1 | 18 | 18 |
| first_seen_frame | 6985 | 27.94 | 2 | 2.0 | 2 | 2 | 2000 | 1 | 2 | 2 |
| object_object_left_right | 1978 | 7.912 | 2 | 2.0 | 2 | 2 | 2000 | 2 | 2 | 2 |
| object_object_near_far | 1982 | 7.928 | 2 | 2.0 | 2 | 2 | 2000 | 2 | 2 | 2 |
| object_object_up_down | 1974 | 7.896 | 2 | 2.0 | 2 | 2 | 2000 | 2 | 2 | 2 |
| object_size | 9778 | 39.112 | 0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| pointing | 20239 | 80.956 | 32 | 32.0 | 32 | 32 | 32000 | 2 | 32 | 32 |
| pose | 194987 | 779.948 | 64 | 64.0 | 64 | 64 | 64000 | 1 | 64 | 64 |
| recovery | 760 | 3.04 | 1 | 1.0 | 1 | 1 | 1000 | 2 | 1 | 1 |
| relative_distance | 20659 | 82.636 | 22.74 | 22.74 | 22 | 23 | 22740 | 2 | 23 | 23 |
| room_size | 425 | 1.7 | 0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| route_planning | 8894 | 35.576 | 9.7 | 9.7 | 9 | 10 | 9700 | 2 | 10 | 10 |
| totals | 0 | 0.0 | 0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| units | 7805 | 31.22 | 2.87 | 2.87 | 2 | 3 | 2870 | 1 | 3 | 3 |

Source for all entries: `work/build16/proofs/census/PLAN_RUN.json`; ceilings: `inputs/mix.json`. Camera displacement/movement/rotation, pose and pointing eligible counts are host substitutes, as above. All 1,000 steps draw 64 pose, 128 VQA, 64 routing and 32 pointing rows. The global largest repeat is 4. Resumed plans equal the corresponding uninterrupted suffixes; absolute step 400 and 600 have identical cell totals but different row-plan hashes, recorded in the plan receipt.

| Changed actual plan draws | Prior total | Current total | Difference |
|---|---:|---:|---:|
| absolute_distance | 5904 | 15600 | +9696 |
| camera_displacement | 21068 | 17420 | -3648 |
| camera_movement_direction | 18431 | 15150 | -3281 |
| camera_rotation | 14727 | 11960 | -2767 |
| counting | 10870 | 10460 | -410 |
| direction | 32890 | 36690 | +3800 |
| totals | 3390 | 0 | -3390 |

Sources: the prior plan retained by build 15, `work/build14/proofs/census/PLAN_RUN.json`, and current `work/build16/proofs/census/PLAN_RUN.json`. The full distance pool removes the prior capacity cut, so distance now receives its entire requested quota and camera cells no longer receive that cut’s refill. The counting/totals changes transfer their freed draws to direction. All other actual plan draw totals are unchanged. Recovery and units retain their requested draws despite the known-K1 population reductions.

`work/build16/proofs/traces/<cell>.jsonl` contains 20 native reader outputs for every available nonempty VQA/slice cell, including zero-quota cells with eligible rows. Each record carries prompt, trace, target, cell, source and row key. Totals and camera-object absolute distance have no eligible rows; camera cells have no real host store. Their files are empty and `INDEX.json` explains why. These examples do not certify RGB grounding where the frame host is absent. Source: `work/build16/proofs/traces/INDEX.json`.

## Persisted handover and CPU proof limits

The reader authenticates h.json from its trusted pin, checks the recorded P run identities and milestone, and rehashes every metadata/export file it consumes. P’s absolute paths remain inside the original JSON bytes; N resolves files by SHA-256. Absent checkpoint state shards remain explicitly listed with their receipt pins. RNG files, layouts, complete.json, stream receipts and indices are checked. Metadata-only admission records missing export bytes and does not claim a weight verification. Sources: `work/tree_r1/student_pilot/r1_persisted.py`, `work/build16/proofs/final_focused/b16/`, `work/build16/proofs/edges/TESTS.json`.

The synthetic P fixture uses the native legacy checkpoint/export and unchanged receipt producer, then relocates the persisted files and omits state shards from N’s view. Native N readers admit absolute steps 400 and 600. Separate tests load LM weights and 192 head tensors from the relocated tiny export. Forged preparation/config/complete pins, altered file bytes, untrusted receipts, incomplete stream closures, path escapes and mismatched export manifests refuse by name. Sources: `work/build16/proofs/final_focused/TESTS.json`, `work/build16/final_focused.log`, `work/build16/proofs/edges/TESTS.json`.

The resumed forward component exercises native `Rows.row/get`, `fetch`, the sampler, full tiny-model forward and loss for every rank. Stand-ins replace host metadata, RGB/tokenizer encoding and pretrained weights; native preparation is not executed in that test. The tiny model loads P’s LM, while head-loading equality is a separate test. This is not the requested complete production-mode fixture. Source: `work/build16/proofs/final_focused/b16/persisted_400/FORWARD.json`.

| Stream | Mean loss | Min loss | Max loss | Draws |
|---|---:|---:|---:|---:|
| pointing | 4.186718463897705 | 4.186718463897705 | 4.186718463897705 | 32 |
| pose | 0.8962479829788208 | 0.8962479829788208 | 0.8962479829788208 | 64 |
| routing | 0.0 | 0.0 | 0.0 | 64 |
| vqa | 4.186718463897705 | 4.186718463897705 | 4.186718463897705 | 128 |

The component records peak RSS 459493376 bytes and absolute step 400. Source: the same `FORWARD.json`; these are synthetic CPU results, not 9B memory measurements.

## Operator packet

`work/build16/proofs/operator/OPERATOR.md` gives the staging table, P persistence procedure, P config locations, initialization blockers and invocation. `STAGING.json` lists each reachable pin’s source path, opaque staged name, size and SHA-256. Missing inputs have null sizes. The final kit’s control/source files are additionally enumerated in its `SHA256SUMS.txt`; the actual P export tar has no supplied pin or size. The packet is therefore an inventory of available and required inputs, not a completed staging manifest for a real job.

The kit’s separate q mode verifies staged pins, invokes native routing build/composition and prepare through s1_admission, binds the native reader population, audits its production plan, derives the final N handover mapping, and reads P’s persisted handover. Optional weights enable every rank’s first resumed CPU batch and loss. One RESULT.json records admission/refusal, stage results, absolute step, losses and peak RSS. The job script requests one general-partition CPU task, eight CPUs and 20 GiB; admission caps address space at 19 GiB. No GPU fit was measured or GPU fallback justified. Sources: `work/tree_r1/launch_r1/production_proof.py`, `work/build16/proofs/operator/j.sh`.

The mode control-flow unit test verifies pin relocation remains active through preparation, population binding, audit and final handover. It replaces those three native preparation/audit phases, so its ADMIT result is not a native end-to-end proof. Source: `work/build16/proofs/mode_unit/TESTS.json`, `work/build16/mode_test16.py`.

All fresh kits pass the inherited opaque-name scanner and remain GO=false. The human-readable report and packet stay outside the job-visible kit. No scheduler, Orchard, GCS or network call was made. Source: `work/build16/KIT_RESULT.json`.

## Exact JSON and preserved behavior

Only the packet test compares the independently recomputed generator output to the baseline JSON: `work/contracts_r6/packet_root/work/tests_r6/test_generator_r4.py:15`. No trainer/admission/loader consumer of that baseline was found. Runtime exact identities do exist: `r1_population.py:84`, `r2_intake.py:87`, `r2_contract.py:85,135,211`, and `p3_provenance.py:49` under `work/tree_r1/student_pilot/`. These authenticate stored parsed values or pinned bytes; they do not independently recompute the floating geometry checked by the packet. Stored-value JSON round-trip and equivalent formatting pass. No runtime tolerance or packet assertion was changed. Source: `work/build16/proofs/float/RESULT.json`.

The native model forward, training loop, export/checkpoint, preparation, reader and fetch functions remain byte-equal where recorded. The P receipt producer/collector, Unicode rules, intake, routing composition, sampler and keep-opener gates retain their build-15 bytes. N retains parent step 544 (`1d6eeb28...`), all sealed exclusions, the 601-row list, scale weight 0.04, M1/L1 contracts, effective-value comparison and default-deny handover. A, C and C′ still admit with their forbidden config mutations refused. Sources: `work/build16/proofs/preservation/RESULT.json`, `proofs/real/RESULT.json`, `proofs/final_focused/TESTS.json`.

## Tests, coverage and delivery

Focused tests: 71 passed. Additional edge tests: 4 passed. Frozen R2 group: 449 tests, 449 passed, 0 failures, 0 errors. Packet: 200 passed and 2 failed, with 0 newly failing packet cases versus build 15. Sources: `proofs/final_focused/TESTS.json`, `proofs/edges/TESTS.json`, `proofs/final/suite_tree/r2/results.json`, `proofs/final/packet/results.json`, all under `work/build16/`; comparison: `work/build15/proofs/final/packet/results.json`.

The packet failures remain the exact floating serialization comparison and the absent attack_decode input. No observed regression was introduced in the executed suites. This does not assert zero regressions in unavailable groups; BF16 parity remains unchecked. All 13 guard mutations are caught using one reused mutant tree. Source: `work/build16/proofs/mutations/RESULT.json`.

Current-file observations cover **287/304 changed production statement heads against build 15**. Unobserved lines remain listed in `DELTA_COVERAGE.json`; the full production-mode success path is among the gaps. Cumulative coverage against the original tree is **7679/7907**, with separate gap classes in `CHANGED_COVERAGE.json` and `GAPS.json`. The standard-library monitor validates compiled-source fingerprints and source hashes. No claim of complete changed-statement coverage is made. Sources: `work/build16/DELTA_COVERAGE.json`, `CHANGED_COVERAGE.json`, `GAPS.json`.

Source seal: `04e21e92987325d6f1538ddeeeb4e01fc9cec180bb5db422be57c8717c1d1b00`. Archive: `out/tree_rebuild_b16_04e21e92.tar` (gzip). The external `work/build16/DELIVERY.json` records archive bytes and SHA-256; `proofs/integrity/RESULT.json` records stream verification after packaging. These external receipts cannot be included in their own archive.

| Kit | SHA-256 | GO |
|---|---|---|
| a2 | `f35e272761d81d52d38fffb41664e15eb88a7c320405ce9bcb462646cd1be598` | false |
| a0 | `73593552f1749647c9c7cd41cb34601fa3f65af01bdfaae401592b68b26c2d21` | false |
| r1 | `9b40645290cafea96b80a54580118d76d1911781180a1eb51c5f57043d2d75fb` | false |

Source: `work/build16/KIT_RESULT.json`. Each final kit was staged from an empty destination. `STORAGE.json`, per-test storage receipts and the external integrity receipt record workspace/temp limits. No real checkpoint, database, cache or frame set was copied. Real rows were streamed for the census; only counts, hashes, bounded examples and plans were retained.

## Not checked or absent

- not rerun: input absent (/scratch/jjyeung/n30_mirror/b12_cntapp/work/auth/K1SPLIT_R0.json).
- not rerun: input absent (/scratch/jjyeung/n30_mirror/rows_a2/work/alias_map.json).
- not rerun: input absent (/scratch/jjyeung/n30_mirror/b12_cntapp/work/d3_token_map.json).
- not rerun: input absent (/scratch/jjyeung/orch_cd/ground_backend/work/c1mix_sb/student_pilot/ground_lifting.py).
- not rerun: input absent (/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/MANIFEST.json).
- not rerun: input absent (/scratch/jjyeung/orch_n30/review_contracts/work/mytests/attack_decode.py).
- not rerun: input absent (/scratch/jjyeung/orch_n30/review_tree11/work/parity/geo_dump.py).

Sources: `work/build16/INPUTS.json`, `SUITE_RUNS.json`, `proofs/final/packet/results.json`, `proofs/preservation/RESULT.json`. `proofs/operator/STAGING.json` lists the exact absent frame-host paths. The operator’s real milestone export and trusted receipt have no supplied local path. Full production admission, full RGB/9B forward, complete K1 resolution, camera trace samples and the single native-mode CPU fixture remain unqualified.

## For the confirmation

Run these commands from the package root with the supplied environment. Each proof uses a fixed output folder. The packet command is expected to record the qualified failures above. No command submits a job.

```bash
B16_PROOF=final_focused bash work/build16/run.sh work/build16/test16.py tests.test_r1_build16 tests.test_r1_build15 tests.test_r1_build14 tests.test_r2_build_n1 tests.test_r2_n1fix tests.test_r2_n1fix3 tests.test_r2_build12 tests.test_r1_build13 tests.test_r2_build3.Build3.test_opener_export_keep_and_reset
B16_PROOF=edges bash work/build16/run.sh work/build16/test16.py edge_test16.Edges stage_test16.Staging
bash work/build16/run.sh work/build16/real16.py
bash work/build16/run.sh work/build16/float16.py
bash work/build16/run.sh work/build16/mutations16.py
bash work/build16/run.sh work/build16/packet16.py integrated packet
bash work/build16/run.sh work/build16/suite16.py
bash work/build16/run.sh work/build16/preserve16.py
bash work/build16/run.sh work/build16/coverage16.py
bash work/build16/run.sh work/build16/delta_coverage16.py
bash work/build16/run.sh work/build16/integrity16.py
```

`census16.py` reproduces the full-stream census only when the pinned real inputs remain available and that scan is authorized. `inputs16.py` is a build-time binding step. Use `kits16.py` only with an empty kit destination. The operator’s frame-host command is `bash b/q.sh /tmp/<opaque-new-root> /tmp/<opaque-request>.json`; the request must first resolve the missing authorities, staged inputs and P export. The complete host proof remains a prerequisite to production admission.
