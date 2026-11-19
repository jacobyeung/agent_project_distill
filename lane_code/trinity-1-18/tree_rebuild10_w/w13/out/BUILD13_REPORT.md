# Build 13

The R1 population producer and N routing composition are implemented and CPU-qualified. GO=false: production admission still requires the real frame host, verified remote slice sources, catalogs and coverage. Trinity cannot certify the full production audit. Source: `work/build13/proofs/tests/results.json`; `work/build13/KIT_RESULT.json`.

## Changes

| Change | State | Evidence |
|---|---|---|
| Population after native preparation, source-identity cells, complete disjoint reader offsets, mixed pose support and binding publication | Closed in code and CPU proofs | `student_pilot/r1_population.py`; `work/build13/proofs/census/`; `work/build13/proofs/tests/` |
| Native routing base composition with N slices; original distance/unit rows excluded; membership pinned | Closed in code and CPU proofs | `student_pilot/r1_routing.py`; `work/build13/proofs/builder/RESULT.json`; `work/build13/proofs/composition/RESULT.json` |
| Native routing layout reaches reader and encoder | Closed in CPU proof | `work/build13/proofs/encode/RESULT.json` |
| Host wiring, produced config and audit binding | Implemented; full host run blocked | `student_pilot/s1_admission.py`; `launch_r1/entry.py`; `student_pilot/r1_loader.py` |
| Reader subset preserves original scene evidence | Closed in CPU proof | `student_pilot/s1_exclusions.py`; `work/build13/proofs/edges/RESULT.json` |
| Fresh kits, pinned slice requirements and membership, ordered host request | Closed; remote source resolution blocked | `launch_r1/build.py`; `work/build13/KIT_RESULT.json` |
| Refusal tests and mutations | Closed | `tests/test_r1_build13.py`; `work/build13/proofs/mutations/RESULT.json` |
| Portable confirmation fixture resolves the parent artifact inside the package and verifies its unchanged hash | Closed | `tests/test_r2_build12.py`; `work/build13/proofs/fixture_path/TESTS.json` |
| Full RGB/GPU production acceptance, BF16 parity and existing qualification blockers | Blocked; unchanged | `work/build13/SUITE_COMPARISON.json`; `work/build13/KIT_RESULT.json` |

The host composes at native admission, immediately after `s1_routing.build` and before `prepare`. This preserves the native catalogs and selection while giving preparation one routing receipt. The SQLite `rows` view reconstructs the native routing JSON from a payload that stores the repeated ground record once; membership authenticates that reconstructed row. Source: `student_pilot/r1_routing.py`.

## Census reproduction

Every entry below matches the lane audit exactly. Source: `work/build13/proofs/census/CENSUS.json`; reference pin: `/scratch/jjyeung/orch_n30/tree_rebuild_w/work/loader_n/CENSUS.json`.

| Cell | Lane eligible | Producer eligible |
|---|---:|---:|
| appearance_order | 27,587 | 27,587 |
| box_3d | 3,813 | 3,813 |
| camera_object_rel_distance_v1 | 1,930 | 1,930 |
| camera_object_rel_distance_v2 | 1,957 | 1,957 |
| camera_object_rel_distance_v3 | 1,978 | 1,978 |
| counting | 11,295 | 11,295 |
| direction | 49,901 | 49,901 |
| facing_pairs | 43,469 | 43,469 |
| first_seen_frame | 6,985 | 6,985 |
| object_object_left_right | 1,978 | 1,978 |
| object_object_near_far | 1,982 | 1,982 |
| object_object_up_down | 1,974 | 1,974 |
| object_size | 9,778 | 9,778 |
| relative_distance | 20,659 | 20,659 |
| room_size | 425 | 425 |
| route_planning | 8,894 | 8,894 |
| totals | 9,201 | 9,201 |
| absolute_distance slice | 1,476 | 1,476 |
| recovery slice | 777 | 777 |
| units slice | 8,067 | 8,067 |

The VQA scan read 204,413 rows. The exclusion list refused 601 and the ASCII think check refused 6, leaving 203,806. Source: `work/build13/proofs/census/CENSUS.json`.
Slice-source identity overrides the question-type classification for {'recovery': 201} rows. Unit counts are {'cm': 2675, 'ft': 2735, 'in': 2657}. Facing statistics are {'complete_pair_ids': 17479, 'draw_unit': 'single row', 'incomplete_pair_ids': 0, 'pair_ids': 17479, 'rows': 43469}. Source: `work/build13/proofs/census/population/population.json`.
The sealed P classifier agrees on the bounded real-row sample. Source: `work/build13/proofs/mapping/RESULT.json`. Zero-quota cells remain in the population. Facing rows draw singly. Source: `work/build13/proofs/census/population/population.json`.

## Allocation and plans

All 1,000 steps use pose 64, VQA 128, routing 64 and pointing 32. Absolute-distance draws fall from 15,600 to 5,904; camera displacement, movement direction and rotation receive 3,648 / 3,281 / 2,767 additional draws. The largest row repeat is 4. Every allocation equals the lane plan. Source: `work/build13/proofs/census/PLAN_RUN.json`; reference pin: `/scratch/jjyeung/orch_n30/tree_rebuild_w/work/loader_n/ROW_PLAN.json`.

| Cell | Draws across the plan |
|---|---:|
| absolute_distance | 5,904 |
| appearance_order | 14,420 |
| box_3d | 1,820 |
| camera_displacement | 21,068 |
| camera_movement_direction | 18,431 |
| camera_object_abs_distance | 0 |
| camera_object_rel_distance_v1 | 2,000 |
| camera_object_rel_distance_v2 | 2,000 |
| camera_object_rel_distance_v3 | 2,000 |
| camera_rotation | 14,727 |
| counting | 10,870 |
| direction | 32,890 |
| facing_pairs | 18,170 |
| first_seen_frame | 2,000 |
| object_object_left_right | 2,000 |
| object_object_near_far | 2,000 |
| object_object_up_down | 2,000 |
| object_size | 0 |
| pointing | 32,000 |
| pose | 64,000 |
| recovery | 1,000 |
| relative_distance | 22,740 |
| room_size | 0 |
| route_planning | 9,700 |
| totals | 3,390 |
| units | 2,870 |

The camera, pose and pointing populations use the reference counts through synthetic native-reader rows and virtual offsets. They are not a production N census. N scene exclusions may reduce those populations on the host. The composed slice offsets and VQA offsets are real. Source: `work/build13/proofs/census/host_boundary.json`.

## Tests, mutations and coverage

The packet suite passed 202/202 checks. Source: `work/build13/proofs/final/packet/results.json`.
The frozen suite ran 2334 tests: 1766 passed, 145 skipped, 501 preexisting failure events, 1 regression events and 0 R2 failures. The BF16 parity failure remains blocked. Source: `work/build13/SUITE_COMPARISON.json`. Failure-event counts include subtests and setup/import errors; they need not sum to test executions.

The untouched base ran 1842 tests: 1275 passed, 145 skipped, 12 failure events and 489 error events. Its receipts are reused only after exact source/fixture checks and runner equivalence. Source: `work/build13/proofs/final/suite_base/results.json`; `work/build13/proofs/final/suite_base/RESUME_RECEIPT.json`.

| Mutation | Result |
|---|---|
| unassigned | CAUGHT |
| slice_identity | CAUGHT |
| overlap | CAUGHT |
| binding | CAUGHT |
| base_cell | CAUGHT |
| base_composition | CAUGHT |

Source for every mutation result: `work/build13/proofs/mutations/RESULT.json`. Each clean targeted test passed before its mutant ran; all mutants reuse one tree directory.

Coverage spans 7509 changed statement heads since the untouched base. Source: `work/build13/CHANGED_COVERAGE.json`.

CPU-reachable unresolved statements: 0. Source: `work/build13/GAPS.json`.

| Coverage class | Statements |
|---|---:|
| observed | 7256 |
| unreachable-after-sealed-refusal | 3 |
| frame-host | 240 |
| GPU | 7 |
| model-loader | 2 |
| compile-time declaration | 1 |

Coverage uses standard-library compiled-source tracing and excludes top-level test files, as in build 12. Prior observations transfer only with exact file bytes or an identical complete function, and each transfer records hashes. Frame-host, GPU and model-loader gaps remain explicit. Scope declarations have no runtime instruction. Source: `work/build13/coverage13.py`; `work/build13/CHANGED_COVERAGE.json`.

## Preserved behavior

N retains its step-544 / 1d6eeb28 launch binding. Handover default-deny, receipt checks, Unicode rules, M1 binding and L1 refusals remain. Original-family text/reader/intake counts remain 1532/0/0, 2000/1186/1102, 2000/1222/1119 and 476/0/431. The 601-key exclusion and 144,000/144,000 parity sweep retain authenticated build-12 evidence; they were not rerun as full real-row proofs. Repaired-family counts were reproduced above. Sources: `work/build13/PRESERVATION.json`; `work/build12/PROOF_EQUALITY.json`; `work/build12/proofs/preservation/RESULT.json`; `work/build12/proofs/depth_sweep/RESULT.json`.

No inference selector, guard, fallback or agent loop was added. Changes concern training admission and sampling; native model forward paths and top-level training functions retain their source. Source: `work/build13/PRESERVATION.json`.

## Kits and operator sequence

All kits were staged from empty and remain GO=false. Their hashes come from `work/build13/KIT_RESULT.json`.

| Kit | Kit SHA-256 | Source SHA-256 |
|---|---|---|
| a2 | `a3ae86c9d5d5f5b50c1e965fc9976ccdb8385b5b0b25d297b871520b16d3e3c5` | `35d4b18b033da1be95c6453469330537578155abd17ecb10e850765729f187ad` |
| a0 | `a1cb45efc50fba173b642de28698ac150c249249f4e51d4a8c53f7fcb2a5b7bc` | `35d4b18b033da1be95c6453469330537578155abd17ecb10e850765729f187ad` |
| r1 | `5755603afaf9a523178aa41d8abfe651e62bf6440b83755360be6e776ded1dea` | `35d4b18b033da1be95c6453469330537578155abd17ecb10e850765729f187ad` |

The operator must verify the remote sources against the staged pins and resolve the native base, source manifests, frame maps and independent scene coverage. On the real frame host, set `STUDENT_R2_FRAME_HOST=1`, `STUDENT_R2_LOCAL_NODE=0` and `CUDA_VISIBLE_DEVICES=""`; the native intake guard requires this host declaration and still refuses full intake on Trinity. Source: `student_pilot/r2_intake.py`. Then run these host steps in order through `launch_r1.entry.frame_host`:

1. Run native `s1_routing.build`, then `r1_routing.compose_native` with the verified source manifests.
2. Run native `carrier_c1_run.prepare` through `s1_admission` on the composed routing receipt.
3. Run `r1_population.bind_prepared` on the prepared configuration; use its returned configuration and preparation receipt.
4. Run `r1_loader.production_audit` on that returned configuration. Missing or changed bindings refuse. Trinity remains prohibited for this full audit.

The exact request and unresolved parameters are in `work/build13/kits/r1/` and `work/build13/KIT_RESULT.json`. Do not launch from the pre-producer config.

## Limits and stand-ins

The native builder proof uses a bounded source fixture and synthetic host frame metadata; the encoding proof substitutes RGB frame loading and the pretrained processor only. The census uses published scene coverage as the lane did, placeholder frame pins, and GUESS 24 FPS where source metadata is absent. It does not establish independent frame-host coverage or real-scene numeric parity. Sources: `work/build13/proofs/builder/RESULT.json`; `work/build13/proofs/encode/RESULT.json`; `work/build13/proofs/census/CENSUS.json`.

No full host admission, production P weights, GPU/pretrained tower execution, independent full-store scene audit, remote upload, submission, Orchard call or GCS call was performed. Existing product-inference and FRAME64 blockers remain. Sources: `work/build13/KIT_RESULT.json`; `work/build13/CHANGED_COVERAGE.json`.

Superseded owned kit copies were overwritten with digest receipts; active kits retain their verified bytes. Final workspace usage and projected archive-extraction growth are checked explicitly. Peak workspace usage during the earlier extraction was not measured. Sources: `work/build13/RETAINED_KIT_RECEIPTS.json`; `work/build13/STORAGE.json`; `work/build13/package13.py`.

## For the confirmation

Run from the package root on the permitted compute node. Each command uses the bounded runner and fixed proof folders. The full census needs the named read-only external inputs; the archive does not carry their databases or raw slices.

```bash
bash work/build13/run.sh work/build13/test13.py
bash work/build13/run.sh work/build13/census13.py
bash work/build13/run.sh work/build13/native_builder13.py
bash work/build13/run.sh work/build13/recompose13.py
bash work/build13/run.sh work/build13/census13.py --resume
bash work/build13/run.sh work/build13/encode13.py
bash work/build13/run.sh work/build13/mapping13.py
bash work/build13/run.sh work/build13/mutations13.py
bash work/build13/run.sh work/build13/preserve13.py
bash work/build13/run.sh work/build13/edges13.py
bash work/build13/run.sh work/build13/packet_inputs13.py
bash work/build13/run.sh work/build13/packet13.py integrated packet contract
bash work/build13/run.sh work/build13/package13.py out/tree_rebuild_b13_35d4b18b.tar
bash work/build13/run.sh work/build13/compare13.py
bash work/build13/run.sh work/build13/coverage13.py
bash work/build13/run.sh work/build13/storage13.py
```

Fresh kit staging is reproduced with `kits13.py` from an empty `work/build13/kits`; preserve any existing kit directory before rerunning it. Source sealing uses `work/n1fix2/seal.py`; archive production uses `work/build13/delivery13.py`. Never use the supplied production host entry on Trinity.

The final source seal is `35d4b18b033da1be95c6453469330537578155abd17ecb10e850765729f187ad`. Inventory and base comparison are `out/TREE_FILES.sha256` and `out/TREE.diff`. The package path, byte count and checksum are recorded in `work/build13/DELIVERY.json`.
