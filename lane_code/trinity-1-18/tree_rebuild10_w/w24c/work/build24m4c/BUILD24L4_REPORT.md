Tree seal: 0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de; 944 files.
Checked all 20 production consumers (CONSUMERS24L4.json); only r1_launch22.py needs a change; all 19 others support 13 lists unchanged.
The validator accepts REMOVAL_ORDER or REMOVAL_ORDER[:-1] + (POINTING_K1_REMOVE, NAMING_REMOVE), with POINTING_K1_REMOVE=d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1.
Spec equality, naming last/once and pinned naming authentication remain mandatory; other hashes, positions and extra duplicates refuse R1_NAMING_REMOVAL_ORDER.
Unchanged: row_removals.py, ground_target_filter.py and carrier_c1_data.py use dynamic lists/reports; carrier_c1_run.py checks complete receipt pins and clean rows.
Unchanged: r1_rooms.py checks matching audit pins and relative V7/N order; r1_coverage.py delegates validation and verify_union preserves base/union/N counts and relative order.
Unchanged: r1_routing.py and scene_division_gate.py apply all removal pins; s1_pool.py, s1_pool_relocate.py, s1_routing.py and s1_admission.py iterate/forward complete lists.
Unchanged: grounding_targets.py, grounding_train.py and stageb_mdg.py pass/check complete target-filter settings; r2_scene_bindings.py forwards the pool removal spec.
Unchanged: r1_handover.py permits row-input rebinding; launch_r1/build.py stages every pin; launch_s1/build.py enumerates every pin into its catalog.
remove_files is one list shared by all streams: explicit keys determine removal. The pointing-list fixture removes its pointing row and leaves VQA and pose rows unchanged; it adds no scene-wide exclusion or stream exemption.
All 56 focused tests pass: 12 new removal tests plus all 44 tests from 24j, 24l, 24n and 24l3; native synthetic-pin tests cover filtering, 13-entry reports, union order and corrupt bytes.
Both scoped runs execute 110 tests: 50 pass and the same 60 missing-fixture errors match 24l3 exactly; there are no new failures or skips.
Of the 60 errors, 35 need work/base/tree_b01ce449/student_pilot/carrier_c1_run.py; TESTS24L4.json records every cause and the snapshot refusal/final acceptance of 13 pins.
The 96ff9a03 snapshot remains untouched (943 files); 942 files remain byte-identical. Only r1_launch22.py changes and tests/test_host24l4.py is added; scoring and all other admission code are unchanged.
The kit must use the exact new order in both remove_files and launch22.removal_order, and regenerate matching room/preparation/target-filter receipts; stale receipts still refuse.
Production naming bytes are mocked only in order-unit tests; filtering uses authentic synthetic pins. The supplied 320-row production list and full production launch were not exercised.
UNCHANGED24L4.json records every file hash; both patches replay exactly. Requested baseline identifiers are retained to identify and verify the delivery.
Delivery: tree_rebuild_b24l4_0c7614c8.tar; its tree and retained 24l3/24l4 reports are verified against their hashes.
All work stayed under J on trinity-2-28 with nice 10, one-thread libraries and a 19,000,000-KiB memory ceiling; no forbidden services, Git, deletion or other agents were used.
