# Build 14

**Real A/C handover admission is blocked. GO=false.** N binds the lineage scale weight, compares effective config values, and reads milestone exports at their absolute steps. P defaults to resetting routing opener embeddings; N keeps them. Those operations produce different weights, so the required compared key still refuses. Both real-config checks return `P_EXPORT_CONFIG_DIFFERENCE:routing_opener_init`. Sources: `work/build14/proofs/real/RESULT.json`; `work/build14/proofs/opener/RESULT.json`.

## Implementation and acceptance

| Requirement | Result | Evidence |
|---|---|---|
| Scale weight from config and card, focal override only | Implemented; 0.04 is bound in both inputs | `work/build14/INPUTS.json`; `tests/test_r1_build14.py` |
| Effective defaults and file-pin identity | Implemented; unknown missing keys still refuse | `student_pilot/r1_handover.py`; `work/build14/proofs/final_focused/TESTS.json` |
| Audited row/bookkeeping boundary | Implemented with an H1 guard; optimizer, loss, topology and route_table remain compared | Key table below |
| Admit real A and C against the kit | **Blocked by routing_opener_init** | `work/build14/proofs/real/RESULT.json` |
| Receipt and sampler resume at the export milestone | Implemented; producer, reader and N resumed plans execute | `work/build14/proofs/final_focused/n1fix/b14_milestones/RESULT.json` |
| Full parity sweep rerun | **Not run: required generator/reference bytes are outside the authorized inputs and absent from the package** | `work/build14/PRESERVATION.json` |

The kit retains `routing_opener_init=keep`. A diagnostic copy using `reset` admits both A and C; that copy is not a staged kit. Changing the kit to reset would overwrite trained opener rows and change the preserved behavior. The native reset function assigns each opener the mean of its constituent token embeddings, while keep returns without that assignment. The CPU counterexample replaces P weights with small embedding tensors; it does not claim to inspect P opener values. Sources: `work/build14/proofs/real/RESULT.json`; `work/build14/proofs/opener/RESULT.json`; `student_pilot/r2_openers.py:38`; `student_pilot/carrier_c1_routing.py:758`.

The native warm start loads the LM before opener initialization. Its subsequent heads phase writes only auxiliary_heads, so it does not undo an opener reset. Sources: `student_pilot/carrier_c1_run.py:821-840,952-959,1000`; the export/keep/reset regression is `tests/test_r2_build3.py:test_opener_export_keep_and_reset`.

## Key decisions

| Key | Decision | Reason | Code line | Test |
|---|---|---|---|---|
| `dev_scene_exclusions` | Boundary | N preparation rechecks the held-out scene exclusions. | `student_pilot/r1_handover.py:11` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `remove_files` | Boundary | N preparation and reader reapply pinned row removals. | `student_pilot/r1_handover.py:12` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `scene_division` | Boundary | N preparation rebinds the admitted train scenes. | `student_pilot/r1_handover.py:13` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `extent_receipt` | Boundary | N routing intake rebinds numeric row evidence. | `student_pilot/r1_handover.py:14` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `scene_coverage` | Boundary | N preparation rechecks scene coverage. | `student_pilot/r1_handover.py:15` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `type_mix` | Boundary | N population producer counts cells and binds the row plan. | `student_pilot/r1_handover.py:16` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `s1_routing` | Boundary | N native routing builder composes a new admitted store. | `student_pilot/r1_handover.py:17` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `s1_route_policy` | Boundary | N preparation authenticates the table; route_table remains compared. | `student_pilot/r1_handover.py:18` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `h1` | Boundary with nested guard | N preparation rebinds row filters and bookkeeping; active own-row mode stays compared. | `student_pilot/r1_handover.py:19` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `continuation` | Boundary | P checkpoint provenance is replaced by N authenticated handover progress. | `student_pilot/r1_handover.py:20` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `milestones` | Boundary | N recipe rebinds export timing, without changing optimizer or loss. | `student_pilot/r1_handover.py:21` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `checkpoint_disk_guard` | Boundary | N disk preflight rebinds checkpoint storage accounting. | `student_pilot/r1_handover.py:22` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `r2_all_stream_exclusions` | Boundary | N preparation rechecks exclusions across every stream. | `student_pilot/r1_handover.py:23` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `r2_scene_rebuild` | Boundary | N preparation rebinds scene-filtered stream receipts. | `student_pilot/r1_handover.py:24` | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |
| `frame_count` | Compared; absent = `32` | Trainer default at `student_pilot/carrier_c1_run.py:811` | `student_pilot/r1_handover.py:30` | `test_defaults_pins_unknowns_and_boundary_keys` |
| `max_pixels` | Compared; absent = `None` | Trainer default at `student_pilot/carrier_c1_data.py:209` | `student_pilot/r1_handover.py:31` | `test_defaults_pins_unknowns_and_boundary_keys` |
| `min_pixels` | Compared; absent = `None` | Trainer default at `student_pilot/carrier_c1_data.py:209` | `student_pilot/r1_handover.py:32` | `test_defaults_pins_unknowns_and_boundary_keys` |
| `geometry_connector` | Compared; absent = `none` | Trainer default at `student_pilot/carrier_c1_run.py:813-815` | `student_pilot/r1_handover.py:33` | `test_defaults_pins_unknowns_and_boundary_keys` |
| `routing_opener_init` | Compared; absent = `reset` | Trainer default at `student_pilot/r2_openers.py:38`; keep and reset differ | `student_pilot/r1_handover.py:34` | `test_defaults_pins_unknowns_and_boundary_keys` |
| `camera_overrides.weight_scale` | Effective comparison; kit binds 0.04 | Preparation stores base camera settings; runtime merges overrides. The prepared lineage value is 0.04 | `student_pilot/r1_training.py:77`; `carrier_c1_run.py:627,716` | `test_scale_card_config_and_override`; `test_effective_camera_and_metadata_refusal`; real A/C |
| Other camera overrides | Only weight_focal 2.0 is allowed in R1 | Any other override refuses even if it names a camera default | `student_pilot/r1_training.py:85` | `test_scale_card_config_and_override` |
| `recipe.milestones` | Boundary | Export timing is rebound; recipe losses, batch, schedule and optimizer settings remain compared | `student_pilot/r1_handover.py:96` | Milestone producer/reader and real A/C diagnostic |
| File pins, including depth_init | Equal SHA-256 identifies equal pinned bytes across paths | Replica reads verify the original digest; other dictionary fields remain compared. Different depth-init bytes still refuse by name | `student_pilot/r1_handover.py:54` | `test_defaults_pins_unknowns_and_boundary_keys`; inherited depth-init refusals |
| Unknown keys, depth_enabled, align, camera, optimizer/loss fields | Compared; differing values refuse | No permission to change topology, loss or optimizer groups | `student_pilot/r1_handover.py:67` | Real refuse set and inherited native group-table tests |

H1 permits only the named row and bookkeeping fields. Unknown H1 fields and a changed faithful-own-row mode refuse. In this trainer, `routing_pose_targets` has no consumer; `camera_types` only selects row processing. N still validates S2 off and refuses faithful own camera rows. Both route-file JSON values match, despite different serialization hashes; the embedded `route_table` remains compared. Sources: `student_pilot/h1_faithful.py:10-24`; `student_pilot/carrier_c1_run.py:703,717,1258`; `work/build14/proofs/opener/RESULT.json`.

The camera defaults come from authenticated preparation metadata, not numeric constants in the comparator. The real comparison uses P’s named preparation receipt and the exact local replica of the pinned parent artifact; it does not rewrite A or C. The optional metadata replicas verify the original SHA-256. Parent metadata records the scale token and scale branch among its trained parameters. Sources: `work/build14/proofs/real/RESULT.json`; `work/build14/proofs/opener/RESULT.json`.

The explicit file-pin rule applies to depth_init: identical pinned bytes at another path admit. This is the scoped exception to the path-only refusal listed in the Build 12 report; different hashes, head initialization metadata and native optimizer-group differences still refuse. Sources: `tests/test_r1_build14.py`; `tests/test_r2_n1fix3.py`; `out/BUILD12_REPORT.md`.

Absent or null pixel-limit config fields leave native DEFAULT_PIXELS active: minimum 128×128 and maximum 384×384 pixels (`student_pilot/pose_samples.py:37`; consumption at `student_pilot/carrier_c1_data.py:209`). The geometry constructor defaults geometry_online to None and attaches no connector (`student_pilot/carrier_c1.py:109,129`); R1 independently forbids geometry extensions.

## Real configurations and refusals

| Config | SHA-256 of supplied file | Kit result | Diagnostic N reset only |
|---|---|---|---|
| A | `9fd188164999788af36d5c6563d47b30351182ce68962b33703995c6ae45b0bb` | `P_EXPORT_CONFIG_DIFFERENCE:routing_opener_init` | ADMIT |
| C | `2152828974490944a1713f5a539e87211f80179f0b5f9254ea9966fc65788733` | `P_EXPORT_CONFIG_DIFFERENCE:routing_opener_init` | ADMIT |

Source: `work/build14/proofs/real/RESULT.json`. A’s supplied file hash is distinct from its trainer configuration identity. The comparison loads the supplied JSON bytes.

| Refuse variant | A | C |
|---|---|---|
| `depth_enabled` | `P_EXPORT_CONFIG_DIFFERENCE:depth_enabled` | `P_EXPORT_CONFIG_DIFFERENCE:depth_enabled` |
| `align` | `P_EXPORT_CONFIG_DIFFERENCE:align` | `P_EXPORT_CONFIG_DIFFERENCE:align` |
| `camera` | `P_EXPORT_CONFIG_DIFFERENCE:camera` | `P_EXPORT_CONFIG_DIFFERENCE:camera` |
| `camera_overrides` | `P_EXPORT_CONFIG_DIFFERENCE:camera_overrides` | `P_EXPORT_CONFIG_DIFFERENCE:camera_overrides` |
| `lm_lr_scale` | `P_EXPORT_LR_SCHEDULE_MISMATCH:lm_lr_scale` | `P_EXPORT_LR_SCHEDULE_MISMATCH:lm_lr_scale` |
| `unknown_extra` | `P_EXPORT_CONFIG_DIFFERENCE:unknown_extra` | `P_EXPORT_CONFIG_DIFFERENCE:unknown_extra` |

Source: `work/build14/proofs/real/RESULT.json`. These mutations use the diagnostic reset target so the opener mismatch cannot hide another refusal.

The same mutations also run against the unchanged kit. None admits. For unknown_extra, the unchanged kit first reports the opener mismatch; the aligned-policy diagnostic proves the independent named unknown-key refusal. Source: `work/build14/proofs/real/RESULT.json`, `refuse_against_kit`.

## Milestone handover

The receipt producer requires an integer artifact step in P’s run milestones and equality with the checkpoint completion step. The reader requires the same receipt step and the complete pinned closure. `progress` and `boundary` already derive the absolute schedule step from the artifact; N’s cell sampler skips the corresponding prefix. The tests compare each resumed N plan with the uninterrupted plan. Sources: `launch_r1/p_handover_receipt.py`; `student_pilot/r1_handover.py`; `student_pilot/r1_training.py`; `work/build14/proofs/final_focused/n1fix/b14_milestones/RESULT.json`.

| Step | Pose position | VQA position | Routing position | Pointing position |
|---|---:|---:|---:|---:|
| 100 | 6400 | 12800 | 6400 | 3200 |
| 200 | 12800 | 25600 | 12800 | 6400 |
| 400 | 25600 | 51200 | 25600 | 12800 |
| 600 | 38400 | 76800 | 38400 | 19200 |

Source: `work/build14/proofs/final_focused/n1fix/b14_milestones/RESULT.json`. The fixture uses the sealed native checkpoint/export functions with a tiny CPU model and local collective stand-ins. A non-milestone export, a different completion step and a different receipt step refuse. This is not publication of a real P receipt.

## Preserved behavior and qualification

The preserved behaviors are the step-544 / 1d6eeb28 parent launch, handover default deny, receipt closure, Unicode rules, M1 fixed-buffer checks, L1 typed refusals, source-identity population cells, disjoint reader offsets, native routing composition, and the host-only production audit. Sources: `out/BUILD13_REPORT.md`; `work/build14/PRESERVATION.json`; `work/build14/proofs/final_focused/TESTS.json`.

Original-family read/reader/intake counts are 1532/0/0, 2000/1186/1102, 2000/1222/1119 and 476/0/431. Repaired slice counts are 777 / 1,476 / 8,067. The removal proof retains all 601 keys. Sources: `work/build14/proofs/text/RESULT.json`; `work/build14/proofs/row_delta/RESULT.json`; `work/build14/proofs/census/CENSUS.json`; `work/build14/proofs/preservation/RESULT.json`.

The census and allocation proof compares every cell with the lane reference. The plan retains 1,000 steps, quotas 64/128/64/32, absolute-distance draws 5,904, camera refill 3,648/3,281/2,767 and maximum repeat 4. Sources: `work/build14/proofs/census/CENSUS.json`; `work/build14/proofs/census/PLAN_RUN.json`. Camera/pose/pointing population offsets remain host-boundary stand-ins, and absent FPS uses GUESS 24 as declared by the census.

The six population/routing guard mutations run with one reused mutant tree. Source: `work/build14/proofs/mutations/RESULT.json`.

Focused final tests: 58; successful: True. Source: `work/build14/proofs/final_focused/TESTS.json`.

Packet suite: 202/202 passed. Source: `work/build14/proofs/final/packet/results.json`.

Frozen suite: 2338 tests; 1770 passed; 145 skipped. Source: `work/build14/proofs/final/suite_tree/results.json`.

Failure events: 501 preexisting; 1 regressions; R2 failures: 0. Source: `work/build14/SUITE_COMPARISON.json`. Events include setup and subtest errors and need not sum to test executions.

- tests.test_gf1_cache.CachedBank.test_parity_cached_vs_online: BF16 cached/online gradient exceeds the supplied relative tolerance; enabled BF16 remains refused

The 144,000/144,000 sweep result is authenticated inherited evidence, not a rerun. Its generator and expected responses are not packaged or authorized external inputs. Source: `work/build14/PRESERVATION.json`; `work/build12/proofs/depth_sweep/RESULT.json`.

## Census and allocation equality

Each cell retains its eligible population and planned draws. Sources: `work/build13/proofs/census/PLAN_RUN.json`; `work/build14/proofs/census/PLAN_RUN.json`; `work/build14/COUNT_EQUALITY.json`.

| Cell | Build 13 eligible | Build 14 eligible | Build 13 draws | Build 14 draws |
|---|---:|---:|---:|---:|
| absolute_distance | 1,476 | 1,476 | 5,904 | 5,904 |
| appearance_order | 27,587 | 27,587 | 14,420 | 14,420 |
| box_3d | 3,813 | 3,813 | 1,820 | 1,820 |
| camera_displacement | 14,020 | 14,020 | 21,068 | 21,068 |
| camera_movement_direction | 12,260 | 12,260 | 18,431 | 18,431 |
| camera_object_abs_distance | 0 | 0 | 0 | 0 |
| camera_object_rel_distance_v1 | 1,930 | 1,930 | 2,000 | 2,000 |
| camera_object_rel_distance_v2 | 1,957 | 1,957 | 2,000 | 2,000 |
| camera_object_rel_distance_v3 | 1,978 | 1,978 | 2,000 | 2,000 |
| camera_rotation | 9,143 | 9,143 | 14,727 | 14,727 |
| counting | 11,295 | 11,295 | 10,870 | 10,870 |
| direction | 49,901 | 49,901 | 32,890 | 32,890 |
| facing_pairs | 43,469 | 43,469 | 18,170 | 18,170 |
| first_seen_frame | 6,985 | 6,985 | 2,000 | 2,000 |
| object_object_left_right | 1,978 | 1,978 | 2,000 | 2,000 |
| object_object_near_far | 1,982 | 1,982 | 2,000 | 2,000 |
| object_object_up_down | 1,974 | 1,974 | 2,000 | 2,000 |
| object_size | 9,778 | 9,778 | 0 | 0 |
| pointing | 20,239 | 20,239 | 32,000 | 32,000 |
| pose | 194,987 | 194,987 | 64,000 | 64,000 |
| recovery | 777 | 777 | 1,000 | 1,000 |
| relative_distance | 20,659 | 20,659 | 22,740 | 22,740 |
| room_size | 425 | 425 | 0 | 0 |
| route_planning | 8,894 | 8,894 | 9,700 | 9,700 |
| totals | 9,201 | 9,201 | 3,390 | 3,390 |
| units | 8,067 | 8,067 | 2,870 | 2,870 |

The VQA scan read 204,413 rows and retained 203,806. It refused 601 excluded rows and 6 non-ASCII traces. Source: `work/build14/proofs/census/CENSUS.json`.

Source identity overrides: `{'recovery': 201}`. Unit counts: `{'cm': 2675, 'ft': 2735, 'in': 2657}`. Facing statistics: `{'complete_pair_ids': 17479, 'draw_unit': 'single row', 'incomplete_pair_ids': 0, 'pair_ids': 17479, 'rows': 43469}`. These equal the prior proof. Sources: `work/build14/proofs/census/population/population.json`; `work/build13/proofs/census/population/population.json`.

The bounded sample agrees with P’s sealed classifier. Zero-quota cells remain reported, and facing rows draw singly. Sources: `work/build14/proofs/mapping/RESULT.json`; `work/build14/proofs/census/population/population.json`.

## Changed-statement coverage

Coverage spans 7554 changed statement heads against the untouched base. Source: `work/build14/CHANGED_COVERAGE.json`.

| Class | Statements |
|---|---:|
| observed | 7344 |
| unreachable-after-sealed-refusal | 3 |
| frame-host | 197 |
| GPU | 7 |
| model-loader | 2 |
| compile-time declaration | 1 |

Source: `work/build14/CHANGED_COVERAGE.json`; `work/build14/GAPS.json`. Standard-library compiled-source monitoring authenticates current observations. Inherited observations transfer only for identical files or complete functions, with hashes recorded. CPU gaps are reported rather than inferred away.

## Kits and package

| Kit | Kit SHA-256 | Source SHA-256 | GO |
|---|---|---|---|
| a2 | `e783daf534b0212dfdf0df70249140749284a0fe4d615d51a529b67a4d914b6d` | `094933b3ccfd2a1057168cf8d9396a5b98ca21ae2851e673ffa15a5c7a8e4492` | false |
| a0 | `c1d06c7bef8171597ef1c15813a5d39a9db7e4d72a48bad1290b970151725a96` | `094933b3ccfd2a1057168cf8d9396a5b98ca21ae2851e673ffa15a5c7a8e4492` | false |
| r1 | `91a83d253b637fabe659f744ced5d3d55648f05f3d36a615ddb8af3780d49044` | `094933b3ccfd2a1057168cf8d9396a5b98ca21ae2851e673ffa15a5c7a8e4492` | false |

Source: `work/build14/KIT_RESULT.json`. All kits are staged from empty. Verified remote sources, frame-host catalogs, full admission, GPU/pretrained execution, BF16 parity and the existing product-inference blockers remain unresolved. No job was submitted.

Source seal: `094933b3ccfd2a1057168cf8d9396a5b98ca21ae2851e673ffa15a5c7a8e4492`. Inventory and base diff: `out/TREE_FILES.sha256`, `out/TREE.diff`. The gzip package path, size and checksum are in the external receipt `work/build14/DELIVERY.json`; that self-referential digest receipt is not embedded in the archive. Source: `out/TREE_SEAL.json`.

The workspace cap is 1,500,000,000 bytes; measured workspace and temporary sizes are recorded in `work/build14/STORAGE.json` and the external final integrity receipt. Temporary storage checks run before and after each test under `ulimit -f 204800`.

Completed early CPU tensor fixtures are retained as digest receipts. Final focused proof tensors, native databases and observation records remain intact. Source: `work/build14/RETAINED_CPU_PRODUCTS.json`.

## For the confirmation

Run from the package root on the permitted compute node. The real-config and full census proofs require the named read-only external inputs. The parity rerun cannot be reproduced from the authorized package inputs.

```bash
bash work/build14/run.sh work/build14/real14.py
bash work/build14/run.sh work/build14/opener14.py
B14_PROOF=final_focused bash work/build14/run.sh work/build14/test14.py tests.test_r1_build14 tests.test_r2_build_n1 tests.test_r2_n1fix tests.test_r2_n1fix3 tests.test_r2_build12 tests.test_r1_build13
bash work/build14/run.sh work/build14/census14.py
bash work/build14/run.sh work/build14/native_builder14.py
bash work/build14/run.sh work/build14/recompose14.py
bash work/build14/run.sh work/build14/census14.py --resume
bash work/build14/run.sh work/build14/encode14.py
bash work/build14/run.sh work/build14/mutations14.py
bash work/build14/run.sh work/build14/text14.py
bash work/build14/run.sh work/build14/row_delta14.py
bash work/build14/run.sh work/build14/preservation14.py
bash work/build14/run.sh work/build14/packet_inputs14.py
bash work/build14/run.sh work/build14/packet14.py integrated packet contract
bash work/build14/run.sh work/build14/compare14.py
bash work/build14/run.sh work/build14/coverage14.py
bash work/build14/run.sh work/build14/storage14.py
```

`final14.py` records the ordered seal, fresh-kit, packet and frozen-suite commands. `package14.py` takes the archive path from `DELIVERY.json`; it reuses a suite group only when source, fixtures, runner and bound inputs match. Run `kits14.py` only with an empty `work/build14/kits` directory. Preserve an existing kit directory before restaging. Source sealing uses `work/n1fix2/seal.py`; packaging uses `work/build14/delivery14.py`.

Additional count and guard checks: `bash work/build14/run.sh work/build14/edges14.py`, `bash work/build14/run.sh work/build14/confusables14.py`, `bash work/build14/run.sh work/build14/mapping14.py`, and `bash work/build14/run.sh work/build14/check_results14.py --require`. Authenticate inherited evidence with `bash work/build14/run.sh work/build14/preserve14.py`. Verify the finished delivery with `bash work/build14/run.sh work/build14/integrity14.py`.
