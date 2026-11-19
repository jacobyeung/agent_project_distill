Patch prepared against the verified base; real composition and fixture-dependent validation remain MISSING.

Base: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`; all 939 files match the supplied seal list.
The overlay changes 10 files. It applies without fuzz and reproduces all 940 resulting files. This delivery contains no production tree seal.

`r1_training.routing_slice_declaration` is an exact path/SHA256 pin to a JSON object with schema `r1-routing-slices-v1`, a `bound` list and a `deferred` object mapping every omitted family to a nonempty reason.
The two sets must partition all six families. Composition orders them as absolute_distance, units, coverage_distance, coverage_units, recovery, camera_wording.
Source, staged-source, envelope and catalog families must match the declaration. Missing envelopes and undeclared families refuse by name.
Project the lane’s source/envelope/catalog dictionaries to the bound families and retain their original pins; report metadata is not a routing family.
Composition and membership receipts retain the declaration pin and deferred reasons. Legacy configurations retain their existing behavior.
The declaration selects families only; it does not waive source pins, exclusions, grammar, extent, membership or host checks.

Camera merge instruction: replace only `CAMERA_SOURCE_SHA256` at `student_pilot/r1_coverage.py:8` with the final authenticated camera file SHA256.
The current stand-in is `31914ba5470c1b5b7fac4ba52a13482cb6ce2965a732b69f6f57a55ed1fbe814` from the supplied `route/out/rows/camera_wording.jsonl`. The final camera SHA is MISSING.
The pin remains a tree constant. The stand-in passes the source check and still requires wording exclusions; the sealed base refuses its source pin.

The frame-host patch adds Q_E7, updates both readers and runtime source obligations, and clears inherited Q_E7 in host/worker entrypoints.
The named NFS ALIAS2.patch is MISSING. The local alias lane’s ALIAS.patch produces the six exact file hashes in FHALIAS2_REPORT.md; ALIAS_REBASE.json records that check.

Portable regressions: base 11 tests; 43 failures, 39 errors, 0 skips; new 11 tests; 0 failures, 0 errors, 0 skips. Subtest failures are counted separately by unittest.
The new regressions cover all 64 subsets, four/five-family composition, deferred receipts, named refusals, declaration relocation, the alias and the camera constant.
Camera source regression: base 1 test; 1 failure, 0 errors, 0 skips; new 1 test; 0 failures, 0 errors, 0 skips.
Real-route checks: base 9 tests; 8 failures, 0 errors, 0 skips; new 9 tests; 6 failures, 0 errors, 0 skips.
Family/source binding checks and real envelope intake preserve the genuine Trinity host veto. The unchanged legacy deferred declaration passes its inline checks.
Full compose_native tests remain MISSING at `/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w22/work/build22/inputs/naming_remove.json`.
Those tests isolate SQLite/base-store assembly; they do not mock the hostname, environment, intake or admission checks. No real composition success is claimed.
Reviewed focused suites: base 115 tests; 0 failures, 101 errors, 0 skips; new 115 tests; 0 failures, 101 errors, 0 skips.
Reviewed integration plus host regression: base 11 tests; 0 failures, 3 errors, 0 skips; new 11 tests; 0 failures, 3 errors, 0 skips.
Their missing fixture root is `/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w21`; the host test requires `fixtures/work/build6/INIT_INPUT.json` there.
Missing imports collapse some requested classes into loader errors; reported test totals include those errors.
Full CPU suite: base 1930 tests; 18 failures, 473 errors, 145 skips; new 1941 tests; 18 failures, 473 errors, 145 skips.
Both full runs used the same CPU harness, which denied worker/subprocess launches, sockets, NFS file reads, deletion and writes outside this workspace.
No new full-suite failures were observed.
BASE_FAILURES.json reports every failing base test/subtest, its cause and traceback. MISSING_INPUTS.json lists exact missing paths and affected tests. TESTS.json contains the comparison.

Commands for every reported number, run from this workspace:
Prefix each Python command below with `env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B`.
`work/verify_base.py` verifies the 939-file seal using the kit’s inventory/digest functions.
`work/build_patch.py` computes file hashes and checks the 10-file patch against all 940 resulting files.
`work/evidence.py` verifies the six reviewed alias file pairs.
`work/run_tests.py base subset_final_base test_r1_subset` and `work/run_tests.py new subset_final_new test_r1_subset` produce the portable counts.
`work/run_tests.py base camera_pin_final_base real_route_tests.RealRoute.test_camera_standin_passes_source_pin_but_requires_wording_exclusions` and the same command with `new camera_pin_final_new` produce the camera counts.
`work/run_tests.py base real_route_final_base real_route_tests` and `work/run_tests.py new real_route_final_new real_route_tests` produce the real-route counts.
`work/run_tests.py base alias_focused_final_base alias-focused` and `work/run_tests.py new alias_focused_final_new alias-focused` produce the focused counts.
`work/run_tests.py base alias_integration_final_base alias-integration` and `work/run_tests.py new alias_integration_final_new alias-integration` produce the integration/host counts.
`work/run_tests.py base full_safe_base full` and `work/run_tests.py new full_final_new full` produce the full-suite counts.
`work/finalize.py` produces failure attribution, comparison, this report, the tar and its SHA256 sidecar.
Use fresh labels/output directories for reruns. Every evidence JSON records its input hashes. No scene mapping, legal admission proof or missing file was invented.

Delivery: PATCH_A.patch, FILES_TOUCHED.json, TESTS.json, REPORT.md, fbp_patchA.tar and fbp_patchA.tar.sha256. The owner must merge, bind the final camera pin, complete missing-input validation and reseal.
