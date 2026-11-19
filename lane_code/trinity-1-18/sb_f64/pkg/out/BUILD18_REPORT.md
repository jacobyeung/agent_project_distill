Native preparation through `s1_admission.admit` refuses both milestones with `ValueError:Missing component evidence: init_m544`; a real job needs complete pinned parent scene manifests, membership receipts and checked-bank intersections, with inherited exposure disclosed.

**GO=false. The requested end-to-end fixture remains incomplete.** Sources: `work/build18/proofs/native/{400,600}/q/RESULT.json`, `work/n1fix2/inputs/EVIDENCE_init_m544.json`, and `work/n1fix2/inputs/registry.json`. The missing evidence is an admission requirement, not a tree defect. The registry also contains other unfilled component records; supplying this first record alone is not a demonstrated route to admission.

## Native mode-q fixture

The driver runs both milestones in one CPU process through `launch_r1.production_proof.run`. It generates native synthetic exports and the metadata subset, writes one weights tar per milestone, reads those tar members back into the persisted export directory, and verifies their pins through the real reader. Checkpoint state shards remain at the producer and are absent from N’s mapped subset. Sources: `work/build18/native18.py`, `work/build18/proofs/native/{400,600}/request.json`.

The frame host supplies synthetic RGB images, frame maps, a frame plan and catalogs. Real `carrier_c1_data.build_stream`, `r2_materialize.materialize`, `carrier_c1_routing.build_routing_stream`, `s1_pool.prepare` and `r2_scene_bindings.rebuild` build their receipts. The processor stand-in is `FixtureProcessor`, a chat-template adapter around `PatchGridProcessor`; it uses the persisted native tokenizer and emits native pixel/grid inputs. Native model dimensions are reduced. CPU local collectives stand in for distributed GPU publication. The native vision encoder constructor needs no substitute. Source: `work/build18/native18.py` and `work/build17/native_assets17.py`.

The frame-host shim returns `fixture-host` from `os.uname` and maps the fixture frame namespace to local synthetic images. At publication, `RunnerTests.local_collectives` supplies local collectives and `fsdp_training.publication_state` returns the tiny model state. These are explicit host/distributed-publication stand-ins; the producer and persisted reader themselves execute unchanged. Source: `work/build18/native18.py`.

The fixture preserves the init-boundary rule: mode q verifies the persisted closure and binds `routing_vocabulary` from the in-job opener before preparation. The final prepared handover reader remains later in the pipeline. The tables report actual observations, including this required ordering. Source: `work/tree_r1/launch_r1/production_proof.py`.

### Milestone 400

Every result below comes from `work/build18/proofs/native/400/q/RESULT.json`. Receipt: `p-export-only-v1` in `work/build18/proofs/native/400/h.json`.

| Stage | Function | Result | Evidence |
|---|---|---|---|
| Staged pins | production_proof.verify_staging | PASS | stage_events |
| Persisted metadata and weights, before prepare | r1_persisted.verify | PASS | stage_events |
| In-job opener bound as routing_vocabulary | p_opener_witness.produce | PASS | q/v.json; q/c.json |
| Native routing build | s1_routing.build | PASS | stage_events |
| Native composition | r1_routing.compose_native | PASS | stage_events |
| Native prepare | s1_admission.admit → carrier_c1_run.prepare | REFUSE: missing init_m544 evidence | refusal; stage_events |
| Prepared population | r1_population.bind_prepared | NOT EXECUTED | absent from stage_events |
| Production audit | r1_loader.production_audit | NOT EXECUTED | absent from stage_events |
| Final prepared persisted handover | r1_persisted.admission | NOT EXECUTED | absent from stage_events |
| N initialization from the extracted export | carrier_c1_run.init_from_artifact | NOT EXECUTED | absent from stage_events |
| Every rank and stream: full forward and loss | production_proof.forward / first_batch_check | NOT EXECUTED | no forward receipt |

### Milestone 600

Every result below comes from `work/build18/proofs/native/600/q/RESULT.json`. Receipt: `p-handover-v1` in `work/build18/proofs/native/600/h.json`.

| Stage | Function | Result | Evidence |
|---|---|---|---|
| Staged pins | production_proof.verify_staging | PASS | stage_events |
| Persisted metadata and weights, before prepare | r1_persisted.verify | PASS | stage_events |
| In-job opener bound as routing_vocabulary | p_opener_witness.produce | PASS | q/v.json; q/c.json |
| Native routing build | s1_routing.build | PASS | stage_events |
| Native composition | r1_routing.compose_native | PASS | stage_events |
| Native prepare | s1_admission.admit → carrier_c1_run.prepare | REFUSE: missing init_m544 evidence | refusal; stage_events |
| Prepared population | r1_population.bind_prepared | NOT EXECUTED | absent from stage_events |
| Production audit | r1_loader.production_audit | NOT EXECUTED | absent from stage_events |
| Final prepared persisted handover | r1_persisted.admission | NOT EXECUTED | absent from stage_events |
| N initialization from the extracted export | carrier_c1_run.init_from_artifact | NOT EXECUTED | absent from stage_events |
| Every rank and stream: full forward and loss | production_proof.forward / first_batch_check | NOT EXECUTED | no forward receipt |

The fixture has not demonstrated population capacity or any downstream all-rank loss. Its stores contain a bounded synthetic population and the inherited synthetic sampling fixture; these are not evidence that the final sampler can satisfy the card. Separate component tests remain separate evidence. No benchmark answer selects a quota or threshold. Source: `work/build18/native18.py`; `work/build18/proofs/native/RESULT.json`.

## Refusal twins

All cases below enter the same mode-q function. The clean controls stop at native preparation, so these are early refusal checks, not twins of a complete ADMIT run.

| Milestone | Change | Result | Evidence |
|---|---|---|---|
| 400 | altered_shard | `ValueError:P_EXPORT_HANDOVER_FILE_MISMATCH:export/model-00001-of-00001.safetensors` | `work/build18/proofs/native/400/twins/altered_shard/RESULT.json` |
| 400 | export_in_training_config | `ValueError:P_EXPORT_ONLY_PROOF_MODE_Q_REQUIRED_TRAINING_REFUSED` | `work/build18/proofs/native/400/twins/export_in_training_config/RESULT.json` |
| 400 | k1_slice | `ValueError:R1_PROOF_ROOM_AUTHORITY_INCOMPLETE` | `work/build18/proofs/native/400/twins/k1_slice/RESULT.json` |
| 400 | missing_model_manifest | `ValueError:Missing or changed pinned input: /scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/build18/proofs/native/400/missing_manifest.json` | `work/build18/proofs/native/400/twins/missing_model_manifest/RESULT.json` |
| 400 | without_z | `ValueError:R1_PROOF_ROOM_AUTHORITY_INCOMPLETE` | `work/build18/proofs/native/400/twins/without_z/RESULT.json` |
| 400 | wrong_h_pin | `ValueError:P_EXPORT_HANDOVER_RECEIPT_UNVERIFIED` | `work/build18/proofs/native/400/twins/wrong_h_pin/RESULT.json` |
| 600 | altered_shard | `ValueError:P_EXPORT_HANDOVER_FILE_MISMATCH:export/model-00001-of-00001.safetensors` | `work/build18/proofs/native/600/twins/altered_shard/RESULT.json` |
| 600 | export_at_stop | `ValueError:P_EXPORT_ONLY_STOP_REQUIRES_CHECKPOINT` | `work/build18/proofs/native/600/twins/export_at_stop/RESULT.json` |
| 600 | k1_slice | `ValueError:R1_PROOF_ROOM_AUTHORITY_INCOMPLETE` | `work/build18/proofs/native/600/twins/k1_slice/RESULT.json` |
| 600 | missing_model_manifest | `ValueError:Missing or changed pinned input: /scratch/jjyeung/orch_n30/tree_rebuild10_w/w18/work/build18/proofs/native/600/missing_manifest.json` | `work/build18/proofs/native/600/twins/missing_model_manifest/RESULT.json` |
| 600 | without_z | `ValueError:R1_PROOF_ROOM_AUTHORITY_INCOMPLETE` | `work/build18/proofs/native/600/twins/without_z/RESULT.json` |
| 600 | wrong_h_pin | `ValueError:P_EXPORT_HANDOVER_RECEIPT_UNVERIFIED` | `work/build18/proofs/native/600/twins/wrong_h_pin/RESULT.json` |

The K1-row and missing-z variants fail the bound audit/config comparison before composition. The component tests separately exercise room rejection and the missing-z population guard. Sources: `tests.test_r1_build17.Composition.test_new_heldout_row_refuses`, `tests.test_r1_build16.Build16.test_producer_refuses_without_z`, and `work/build18/proofs/mutations/RESULT.json`.

## Tree changes and tests

| Change | Reason | Test |
|---|---|---|
| `student_pilot/s1_admission.py` checks the current interop-thread count before setting it | A repeated native admission in the same process otherwise raises PyTorch’s “cannot set number of interop threads” error | `tests.test_r1_build18.Admission18.test_repeated_admission_thread_setup`; mutation `thread_repeat` |
| `student_pilot/r1_rooms.py` requires the pinned v7 list before n.json and binds it to the audit | The resolved K1 rows must not enter N; unresolved v7 remains explicitly scoped to P’s admitted population and build record | `tests.test_r1_build18.Rooms18`; mutations `v7_gate`, `v7_count`, `v7_order`, `v7_audit_binding`, `v7_unremoved`, `v7_keys` |

The existing room-audit test now uses the config with the required v7 list. No admission gate is weakened. Native inference, training, sampler, counting, opener and checkpoint/export implementations retain the byte-equality checks in `work/build18/proofs/preservation/RESULT.json`.

## Pinned v7 rows and census

The N-side list is `work/build18/inputs/u.json`: 2637 unique row keys, each with its canonical and reason `k1_heldout_v7`. Its SHA-256 is `43853165f921d077eab92baaf83f29a69cd4f3efef789249bb8db99893853cf6`. It occurs once before n.json; n.json and z.json retain their order and hashes. Sources: `work/build18/proofs/rooms/RESULT.json`, `work/build18/inputs/config.json:remove_files`.

| Store count | Before list | After list |
|---|---:|---:|
| rows | 204413 | 204413 |
| ok | 82401 | 82401 |
| k1_heldout | 2637 | 2637 |
| r0 | 0 | 0 |
| unresolved | 119375 | 119375 |
| unremoved_hits | 2615 | 0 |

The census resolves 85038 rows: 43779 from row fields and 41259 from aliases. Source: `work/build18/proofs/rooms/RESULT.json:audit_after.store.canonical_from`.

Every count in this table is from `work/build18/proofs/rooms/RESULT.json:audit_before.store,audit_after.store`. Held-out counts describe the source store; unremoved hits describe the configured lists. Canonical resolution by row field and alias, and the unchanged unresolved population, are recorded there. The three full slice streams have no row-key intersection with the new list, as recorded in `slice_v7_key_intersections`.

Unresolved v7 rows remain in the population P admitted, bound to the exact v7 store and its build record. They are not declared overlap-free. Other benchmark, dev, K1 and R0 exclusions remain active. Source: `work/build18/inputs/room_audit.json:certifies`.

| Cell | Eligible | Delta | Rows/step | Ceiling | Source |
|---|---:|---:|---:|---:|---|
| absolute_distance | 7805 | +0 | 15.6 | 31.22 | Q |
| appearance_order | 27587 | +0 | 14.42 | 110.348 | C |
| box_3d | 3813 | +0 | 1.82 | 15.252 | C |
| camera_displacement | 14020 | +0 | 17.42 | 56.08 | Q |
| camera_movement_direction | 12260 | +0 | 15.15 | 49.04 | Q |
| camera_object_abs_distance | 0 | +0 | 0 | 0 | C |
| camera_object_rel_distance_v1 | 1930 | +0 | 2 | 7.72 | C |
| camera_object_rel_distance_v2 | 1957 | +0 | 2 | 7.828 | C |
| camera_object_rel_distance_v3 | 1978 | +0 | 2 | 7.912 | C |
| camera_rotation | 9143 | +0 | 11.96 | 36.572 | Q |
| counting | 2617 | +0 | 10.46 | 10.468 | C |
| direction | 48440 | -1461 | 36.69 | 193.76 | C |
| facing_pairs | 42875 | -594 | 18.17 | 171.5 | C |
| first_seen_frame | 6985 | +0 | 2 | 27.94 | C |
| object_object_left_right | 1978 | +0 | 2 | 7.912 | C |
| object_object_near_far | 1982 | +0 | 2 | 7.928 | C |
| object_object_up_down | 1974 | +0 | 2 | 7.896 | C |
| object_size | 9778 | +0 | 0 | 39.112 | C |
| pointing | 20239 | +0 | 32 | 80.956 | Q |
| pose | 194987 | +0 | 64 | 779.948 | Q |
| recovery | 760 | +0 | 1 | 3.04 | Q |
| relative_distance | 20235 | -424 | 22.74 | 80.94 | C |
| room_size | 425 | +0 | 0 | 1.7 | C |
| route_planning | 8758 | -136 | 9.7 | 35.032 | C |
| totals | 0 | +0 | 0 | 0 | C |
| units | 7805 | +0 | 2.87 | 31.22 | Q |

C: freshly streamed VQA census in `work/build18/proofs/rooms/RESULT.json:eligible_by_cell`. Q: qualified prior counts in `work/build16/proofs/census/PLAN_RUN.json`; their unavailable payloads were not rerun. Deltas compare those same prior counts. The routing slices were streamed for room and key-intersection checks, not a new production population proof. The ceiling is four times eligible divided by one thousand, as required by the bound card policy. No card cell changed and no ceiling required a quota cut. Sources: `work/build18/proofs/rooms/RESULT.json:allocation,card_cells_changed`; `work/build18/inputs/mix.json`.

## Final validation

The final_focused suite ran 95 tests, with 0 failures and 0 errors. Source: `work/build18/proofs/final_focused/TESTS.json`.
The edges suite ran 4 tests, with 0 failures and 0 errors. Source: `work/build18/proofs/edges/TESTS.json`.
The producer_edges suite ran 11 tests, with 0 failures and 0 errors. Source: `work/build18/proofs/producer_edges/TESTS.json`.

The mutation matrix caught 32 mutants, each with a passing clean control and failing mutant. Source: `work/build18/proofs/mutations/RESULT.json`. Changed-statement coverage observed 17 of 17 changed AST statement heads against the authenticated baseline. Standard-library monitoring requires the current source hash and compiled-source fingerprint. Source: `work/build18/DELTA_COVERAGE.json`.

The frozen R2 suite ran 449 tests with 0 failures and 0 errors. The packet has 200 passes and 2 qualified failures. The comparison finds 0 new regressions. Sources: `work/build18/proofs/final/suite_tree/r2/results.json`, `work/build18/proofs/final/packet/results.json`, `work/build18/proofs/regressions/RESULT.json`.

The qualified packet failures remain the exact floating-JSON comparison and the missing external attack_decode input. Generator and legacy groups remain unavailable, as named in `work/build18/SUITE_RUNS.json`; the large real-row parity sweep was not rerun. No absent group is a pass.

Real A, C and C-prime effective-value comparisons admit; incompatible variants refuse. Parent initialization, list order and scale remain checked in `work/build18/proofs/preservation/RESULT.json`. Sources: `work/build18/proofs/real/RESULT.json` and the preservation result. The kits were built from empty directories and passed their scanner/hash verifiers with GO=false. Source: `work/build18/KIT_RESULT.json`.

N retains the step-544 parent `1d6eeb28`, the existing 601-row list and weight_scale=0.04. The inherited K1 and counting lists remain bound. The new list is the only added removal pin; scene exclusions and card cells compare equal. Source: `work/build18/proofs/configuration/RESULT.json`.

This build used no GPU, scheduler, network, Git, SSH or additional agent. The wrapper caps Python resources; each test records temporary storage before and after execution. Storage evidence: `work/build18/STORAGE.json` and the per-test `TESTS.json` files.

## Package

The new seal is `60e6ea72b5e9fcaa3e400e4d57f0816002e541c44c768097ea0303c78fdc5084` (`out/TREE_SEAL.json`). The gzip tar is `out/tree_rebuild_b18_60e6ea72.tar`. Exact size and SHA-256 are in `work/build18/DELIVERY.json`. Omitted generated payloads are described in `work/build18/PACKAGE_OMISSIONS.json`; external inputs and native synthetic binary assets are not promised by this archive.

Run integrity checks from the workspace root: `bash work/build18/run.sh work/build18/integrity18.py`. The checker streams archive members and verifies the seal, reports and kits without extraction. Its result is `work/build18/proofs/integrity/RESULT.json`.

## For the confirmation

The v7 list and the repeated-admission fix are reviewable. The main deliverable is not complete: neither milestone has an end-to-end ADMIT or initialized all-rank losses. A real job needs the missing parent/component evidence and actual host inputs. The fixture must then prove population capacity, complete preparation, final handover, export initialization and every rank’s forward losses. Confirmation cannot treat the successful component tests or early refusal twins as that proof. GO remains false.
