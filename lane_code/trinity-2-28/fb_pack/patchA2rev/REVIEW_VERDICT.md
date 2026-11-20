GO

PATCH_A2 (3ecd924f) fixes both first-review MUSTs, and I found no MUST item. One SHOULD remains (S1). Line numbers refer to base 57a1f14d and to base+PATCH_A2.

## Verified (own code in work/, inputs re-hashed in work/SETUP.json)
1. Apply: PATCH_A2 applies to base with `patch -p1 --fuzz=0`, without offsets. The result (941 files, seal db3c96e9) changes exactly the 11 files of FILES_TOUCHED.json, to the listed hashes. base+PATCH_A+PATCH_A2_DELTA gives the same seal, so the delta equals PATCH_A2 minus PATCH_A.
2. No declaration, base vs A2 (work/harness.py: 8,444 cases per tree, with exception, message, frames, file events and written bytes recorded; work/COMPARE.json):
   - Deferred config: compose_native raises KeyError 'recovery' at the same comprehension (base r1_routing.py:171, A2 :179), after the same 8 opens, and writes nothing.
   - Legacy without routing_inputs: KeyError 'routing_inputs' at the same lookup (base :176, A2 :189), with or without a catalog, after the same opens as base and before any output.
   - All 79 legacy compose_native cases match base in outcome, file events and written bytes; full compositions write byte-identical rows.sqlite, membership.json and receipt.json.
   - source_names: 1,792 cases (256 subsets of 8 names, 7 configs) are identical. validate_binding: 4,096 cases are identical. Membership: all 640 reachable cases have identical outcomes.
   - Of the 2,228 differing cases, 1,957 differ only in traceback lines. The other 271 are the 14 intended camera-pin changes, the 256 unreachable cases of S1, and 1 extra pin read (the Note below S1).
   - The harness flags both first-review bugs on PATCH_A, so it catches that class of change.
3. Declarations, PATCH_A vs A2: 1,131 of 1,150 cases are identical, and the 19 that differ are all camera-pin cases. Schema, pins, subsets and their order, named refusals, receipt identity and membership behave as PATCH_A's review verified.
4. Camera pin (r1_coverage.py:8 = e8cbda99): the final rows pass validate_binding with the 32-template exclusion for legacy and declared s3cam/s6, and compose_native proceeds to the genuine host veto ("Local slices must contain at most 2000 rows"). The stand-in 31914ba5 raises R1_CAMERA_SOURCE_PIN. Stand-in bytes under the final hash raise "Missing or changed pinned input". Final rows without a camera exclusion raise R1_CAMERA_WORDING_REQUIRED. As intended, A2 also refuses the current ro/.../route/out/config/FIRST_BOUNDARY_CANDIDATE.json with R1_CAMERA_SOURCE_PIN, because it binds the stand-in 3 times. Rebind that config to e8cbda99 before launch.
5. Live 189df6ac: PATCH_A2 applies with --fuzz=0 (seal c46b33a7) and changes the same 11 files to the same hashes. The harness finds 0 of 8,444 differences against A2, and the full suite matches live_base apart from the new tests.
6. PATCH_CAMFORM (2167d5d9) applies with --fuzz=0 on A2 and on live A2. Its compose() hunks are disjoint from the delta, all 105 combined unit-test rows pass on both trees, and the harness finds 0 of 8,444 differences against A2.
7. Nothing else changed: PATCH_A and PATCH_A2 trees differ only in r1_coverage.py, r1_routing.py and tests/test_r1_patch_a2.py, which are the delta files at FILES_TOUCHED's hashes.

Tests (sandboxed: no /home or /data* reads, no subprocesses, writes only under work/):
- test_r1_patch_a2 passes on A2, live A2 and camform. On base its 2 legacy tests pass and the camera test fails; on PATCH_A all 3 fail.
- Full discovery, base vs A2, ran with the test-output variables set: 3,640 vs 3,736 rows. Per-method status counts match on all 1,930 methods. The only new rows are the 96 passing rows of test_r1_subset and test_r1_patch_a2.
- A first run without those variables, and live_base vs live A2, match the same way.
- Pre-existing failures are identical on both sides, and none arises in the touched code. The 470 errors come from the sandbox denying subprocesses (117), missing torchvision (102), the missing w21 fixture (53), the provisional scratch-root rule (20) and smaller causes. The 18 failures are in s1_in_job_gate, carrier_c1_t0, storage and 8 others.

## SHOULD
S1. r1_routing.py:75 still calls `source_names(sources, cfg)` unconditionally (base :71 `source_names(sources)`). A direct compose() call with a deferred config therefore diverges from base:
   - With no sources, base raises R1_ROUTING_SLICES_REQUIRED, but A2 writes membership.json, receipt.json and an empty rows.sqlite.
   - With the 3 slice sources, base composes, but A2 raises R1_MINIMAL_SLICE_BOUND.
   The same holds for Membership(minimal=False) with a deferred config (r1_population.py:75, called from r1_routing.py:151). No shipped path reaches either case. compose() has one non-test caller, compose_native (:219), which fails on deferred configs at :179 and refuses any that pass at :180-181. s1_admission.py:214 skips compose_native for deferred configs, and produce() passes minimal=True exactly when the config is deferred (r1_population.py:112,119). Fix: gate :75 as :178 does.
Note: on the deferred produce() path, r1_population.py:75 re-reads the deferred metadata pins once more. The outcome is identical, and nothing extra is written.

## Missing inputs (cases isolated, not dropped)
- Coverage sources ro/n30_mirror/dist_diag/coverage_v2h/COVERAGE_{DISTANCE,UNITS}_V2H.jsonl are absent. The six-family real cases stub only those two pinned reads (harness.py isolate_coverage).
- ro/n30_mirror/rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl is absent.
- The w21 fixture root (fixtures/work/build6/INIT_INPUT.json) is absent here and in the fix build. As a result, 53 modules (test_r1_build14-20, test_r1_export17 and the test_r2_build* family) fail to load on base and A2 alike, and the harness covers the delta's compose paths instead.

## Reproduce (in work/)
setup.py, then run_all.sh, compare.py, runtests.py (unit/focused/discover; set RUNTESTS_OUTPUT_VARS=1 for the second full run) and compare_tests.py. Outputs: SETUP.json, results/*.json, COMPARE.json, tests_out/*.json, TESTS_COMPARE.json.
